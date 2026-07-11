"""Google Drive folder operations manager."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from googlekit.core.constants import DRIVE_FOLDER_MIME, DRIVE_SHORTCUT_MIME
from googlekit.core.exceptions import ValidationError
from googlekit.core.transport import Transport
from googlekit.core.validation import require_non_empty, require_path
from googlekit.gdrive.files import FilesManager
from googlekit.gdrive.models import (
    FILE_FIELDS,
    DriveFile,
    DriveFolder,
    OverwritePolicy,
    shared_drive_params,
)
from googlekit.gdrive.transfers import ProgressCallback

logger = logging.getLogger(__name__)


class FoldersManager:
    """Create folders, nested paths, and recursive directory sync helpers."""

    def __init__(self, transport: Transport, files: FilesManager) -> None:
        self._transport = transport
        self._files = files

    def _service(self) -> Any:
        return self._transport.get_service("drive", "v3")

    @property
    def _sd(self) -> dict[str, bool]:
        return shared_drive_params(self._transport.config.supports_all_drives)

    def create(
        self,
        name: str,
        *,
        parent_id: str | None = None,
        fields: str = FILE_FIELDS,
    ) -> DriveFolder:
        """Create a single folder under ``parent_id`` (or My Drive root)."""
        require_non_empty(name, "name")
        parents = [parent_id] if parent_id else None
        created = self._files.create(
            name,
            mime_type=DRIVE_FOLDER_MIME,
            parents=parents,
            fields=fields,
        )
        return DriveFolder.from_file(created)

    def create_path(
        self,
        path: str,
        *,
        parent_id: str | None = None,
        fields: str = FILE_FIELDS,
    ) -> DriveFolder:
        """Create nested folders from a slash-separated path; reuse existing names."""
        require_non_empty(path, "path")
        parts = [p for p in path.replace("\\", "/").split("/") if p and p != "."]
        if not parts:
            raise ValidationError("path must contain at least one folder name")
        current = parent_id
        folder: DriveFolder | None = None
        for part in parts:
            existing = self._files.find_by_name(
                part,
                # Scope to My Drive root when no parent was given (not all of Drive).
                parents=[current] if current else ["root"],
                mime_type=DRIVE_FOLDER_MIME,
            )
            if existing is not None:
                folder = DriveFolder.from_file(existing)
                current = existing.id
                continue
            folder = self.create(part, parent_id=current, fields=fields)
            current = folder.id
        assert folder is not None
        return folder

    def list_children(
        self,
        folder_id: str = "root",
        *,
        include_folders: bool = True,
        include_files: bool = True,
        include_trashed: bool = False,
        page_size: int = 100,
    ) -> list[DriveFile]:
        """List immediate children of a folder (eager; use files.iterate for lazy)."""
        require_non_empty(folder_id, "folder_id")
        if not include_folders and not include_files:
            return []
        parts: list[str] = []
        if include_folders and not include_files:
            parts.append(f"mimeType = '{DRIVE_FOLDER_MIME}'")
        elif include_files and not include_folders:
            parts.append(f"mimeType != '{DRIVE_FOLDER_MIME}'")
        query = " and ".join(parts) if parts else None
        return list(
            self._files.iterate(
                query=query,
                folder_id=folder_id,
                page_size=page_size,
                include_trashed=include_trashed,
            )
        )

    def upload_directory(
        self,
        local_path: str | Path,
        *,
        parent_id: str | None = None,
        overwrite: OverwritePolicy | str = OverwritePolicy.ERROR,
        progress: ProgressCallback | None = None,
        create_root: bool = True,
    ) -> DriveFolder:
        """Recursively upload a local directory tree into Drive."""
        root = require_path(local_path, must_exist=True)
        if not root.is_dir():
            raise ValidationError(f"Not a directory: {root}")
        policy = OverwritePolicy(overwrite)
        if create_root:
            existing_root = self._files.find_by_name(
                root.name,
                parents=[parent_id] if parent_id else ["root"],
                mime_type=DRIVE_FOLDER_MIME,
            )
            if existing_root is not None:
                if policy is OverwritePolicy.ERROR:
                    raise ValidationError(
                        f"Remote folder already exists: {root.name!r}. "
                        "Pass overwrite=OverwritePolicy.OVERWRITE or SKIP."
                    )
                destination = DriveFolder.from_file(existing_root)
                dest_id = destination.id
            else:
                destination = self.create(root.name, parent_id=parent_id)
                dest_id = destination.id
        else:
            if parent_id is None:
                raise ValidationError("parent_id is required when create_root=False")
            destination = DriveFolder(id=parent_id, name=root.name)
            dest_id = parent_id

        seen: set[Path] = set()
        self._upload_tree(root, dest_id, policy=policy, progress=progress, seen=seen)
        return destination

    def download_directory(
        self,
        folder_id: str,
        destination: str | Path,
        *,
        overwrite: OverwritePolicy | str = OverwritePolicy.ERROR,
        progress: ProgressCallback | None = None,
        max_depth: int = 50,
    ) -> Path:
        """Recursively download a Drive folder tree to a local directory."""
        require_non_empty(folder_id, "folder_id")
        dest = Path(destination)
        dest.mkdir(parents=True, exist_ok=True)
        policy = OverwritePolicy(overwrite)
        visited: set[str] = set()
        self._download_tree(
            folder_id,
            dest,
            policy=policy,
            progress=progress,
            visited=visited,
            depth=0,
            max_depth=max_depth,
        )
        return dest

    def _upload_tree(
        self,
        local_dir: Path,
        drive_folder_id: str,
        *,
        policy: OverwritePolicy,
        progress: ProgressCallback | None,
        seen: set[Path],
    ) -> None:
        resolved = local_dir.resolve()
        if resolved in seen:
            logger.warning("Skipping recursion loop at %s", resolved)
            return
        seen.add(resolved)

        for item in sorted(local_dir.iterdir(), key=lambda p: p.name.lower()):
            if item.is_symlink():
                # Avoid following symlink cycles into unexpected trees.
                target = item.resolve()
                if target in seen or not item.exists():
                    logger.warning("Skipping symlink cycle or broken link: %s", item)
                    continue
            if item.is_dir():
                existing = self._files.find_by_name(
                    item.name,
                    parents=[drive_folder_id],
                    mime_type=DRIVE_FOLDER_MIME,
                )
                if existing is not None:
                    if policy is OverwritePolicy.SKIP:
                        # Still recurse into existing folder to sync children.
                        sub_id = existing.id
                    elif policy is OverwritePolicy.ERROR:
                        raise ValidationError(
                            f"Remote folder already exists: {item.name!r} under {drive_folder_id}. "
                            "Pass overwrite=OverwritePolicy.OVERWRITE or SKIP."
                        )
                    else:
                        sub_id = existing.id
                else:
                    sub = self.create(item.name, parent_id=drive_folder_id)
                    sub_id = sub.id
                self._upload_tree(
                    item,
                    sub_id,
                    policy=policy,
                    progress=progress,
                    seen=seen,
                )
            elif item.is_file():
                self._files.upload_path(
                    item,
                    parents=[drive_folder_id],
                    overwrite=policy,
                    progress=progress,
                )

    def _download_tree(
        self,
        folder_id: str,
        local_dir: Path,
        *,
        policy: OverwritePolicy,
        progress: ProgressCallback | None,
        visited: set[str],
        depth: int,
        max_depth: int,
    ) -> None:
        if folder_id in visited:
            logger.warning("Skipping Drive folder cycle at %s", folder_id)
            return
        if depth > max_depth:
            raise ValidationError(f"Maximum folder depth {max_depth} exceeded while downloading")
        visited.add(folder_id)
        local_dir.mkdir(parents=True, exist_ok=True)

        for child in self.list_children(folder_id):
            if child.mime_type == DRIVE_SHORTCUT_MIME:
                logger.debug("Skipping shortcut %s (%s)", child.name, child.id)
                continue
            if child.is_folder:
                self._download_tree(
                    child.id,
                    local_dir / child.name,
                    policy=policy,
                    progress=progress,
                    visited=visited,
                    depth=depth + 1,
                    max_depth=max_depth,
                )
                continue
            if child.is_google_native:
                # Default export Google Docs/Sheets/Slides to PDF when syncing trees.
                target = local_dir / f"{child.name}.pdf"
            else:
                target = local_dir / child.name
            if target.exists():
                if policy is OverwritePolicy.SKIP:
                    continue
                if policy is OverwritePolicy.ERROR:
                    raise ValidationError(
                        f"Local file already exists: {target}. "
                        "Pass overwrite=OverwritePolicy.OVERWRITE or SKIP."
                    )
            if child.is_google_native:
                self._files.export(
                    child.id,
                    "pdf",
                    target,
                    progress=progress,
                )
            else:
                self._files.download_path(child.id, target, progress=progress)
