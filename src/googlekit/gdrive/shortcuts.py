"""PyDrive4-style convenience shortcuts for DriveClient.

These delegate to ``files`` / ``folders`` / ``permissions`` managers. Prefer
managers for advanced options; use shortcuts for simple scripts.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from googlekit.core.constants import DEFAULT_PAGE_SIZE, DRIVE_FOLDER_MIME
from googlekit.core.exceptions import ValidationError
from googlekit.core.pagination import Page
from googlekit.core.validation import require_non_empty
from googlekit.gdrive.models import (
    DownloadResult,
    DriveFile,
    DriveFolder,
    OverwritePolicy,
    Permission,
    PermissionRole,
    UploadResult,
)
from googlekit.gdrive.transfers import ProgressCallback

if TYPE_CHECKING:
    from googlekit.gdrive.client import DriveClient


def _escape_drive_query_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


class DriveShortcuts:
    """Optional flat helpers mixed into :class:`~googlekit.gdrive.client.DriveClient`."""

    def list_files(
        self: DriveClient,
        *,
        folder_id: str | None = "root",
        query: str | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
        page_token: str | None = None,
        include_trashed: bool = False,
    ) -> Page[DriveFile]:
        """List files (and folders) in a Drive folder — one page.

        Args:
            folder_id: Parent folder id, or ``\"root\"`` for My Drive root.
                Pass ``None`` to search across Drive with ``query`` only.
            query: Extra Drive query language filter.
            page_size: Max items in this page.
            page_token: Continue from a previous page.
            include_trashed: Include trashed items when True.

        Returns:
            :class:`~googlekit.core.pagination.Page` of :class:`~googlekit.gdrive.models.DriveFile`.

        Note:
            Default OAuth ``READWRITE`` uses ``drive.file`` and may return an empty
            list. Use ``ScopeProfile.FULL`` or ``READONLY`` to see all of My Drive.
        """
        return self.files.list(
            folder_id=folder_id,
            query=query,
            page_size=page_size,
            page_token=page_token,
            include_trashed=include_trashed,
        )

    def list_folders(
        self: DriveClient,
        *,
        folder_id: str | None = "root",
        page_size: int = DEFAULT_PAGE_SIZE,
        page_token: str | None = None,
    ) -> Page[DriveFile]:
        """List only folders under ``folder_id`` (default My Drive root).

        Args:
            folder_id: Parent folder id, or ``\"root\"``.
            page_size: Max items in this page.
            page_token: Continue from a previous page.

        Returns:
            Page of folder :class:`~googlekit.gdrive.models.DriveFile` items.
        """
        return self.files.list(
            folder_id=folder_id,
            query=f"mimeType='{DRIVE_FOLDER_MIME}'",
            page_size=page_size,
            page_token=page_token,
        )

    def search_files(
        self: DriveClient,
        name_contains: str,
        *,
        page_size: int = DEFAULT_PAGE_SIZE,
        page_token: str | None = None,
    ) -> Page[DriveFile]:
        """Search files/folders whose name contains ``name_contains`` (escaped).

        Args:
            name_contains: Substring matched with Drive ``name contains``.
            page_size: Max items in this page.
            page_token: Continue from a previous page.
        """
        require_non_empty(name_contains, "name_contains")
        safe = _escape_drive_query_value(name_contains)
        return self.files.search(
            f"name contains '{safe}'",
            page_size=page_size,
            page_token=page_token,
        )

    def search_folders(
        self: DriveClient,
        name_contains: str,
        *,
        page_size: int = DEFAULT_PAGE_SIZE,
        page_token: str | None = None,
    ) -> Page[DriveFile]:
        """Search folders whose name contains ``name_contains``.

        Args:
            name_contains: Substring matched with Drive ``name contains``.
            page_size: Max items in this page.
            page_token: Continue from a previous page.
        """
        require_non_empty(name_contains, "name_contains")
        safe = _escape_drive_query_value(name_contains)
        return self.files.search(
            f"mimeType='{DRIVE_FOLDER_MIME}' and name contains '{safe}'",
            page_size=page_size,
            page_token=page_token,
        )

    def create_folder(
        self: DriveClient,
        name: str,
        *,
        parent_id: str | None = None,
    ) -> DriveFolder:
        """Create a folder under ``parent_id`` (or My Drive root).

        Args:
            name: Folder name.
            parent_id: Parent folder id; omit for My Drive root.
        """
        return self.folders.create(name, parent_id=parent_id)

    def upload_file(
        self: DriveClient,
        path: str | Path,
        *,
        folder_id: str | None = None,
        name: str | None = None,
        overwrite: bool | OverwritePolicy | str = False,
        progress: ProgressCallback | None = None,
    ) -> UploadResult | None:
        """Upload a local file to Drive.

        Args:
            path: Local file path.
            folder_id: Destination folder id (root if omitted).
            name: Drive file name (defaults to local basename).
            overwrite: ``True`` / ``\"overwrite\"`` replaces same name;
                ``False`` / ``\"error\"`` raises if a name conflict exists;
                ``\"skip\"`` returns ``None`` when a conflict exists.
            progress: Optional upload progress callback.

        Returns:
            :class:`~googlekit.gdrive.models.UploadResult`, or ``None`` if skipped.
        """
        if overwrite is True:
            policy: OverwritePolicy | str = OverwritePolicy.OVERWRITE
        elif overwrite is False:
            policy = OverwritePolicy.ERROR
        else:
            policy = overwrite
        parents = [folder_id] if folder_id else None
        return self.files.upload_path(
            path,
            parents=parents,
            name=name,
            overwrite=policy,
            progress=progress,
        )

    def download_file(
        self: DriveClient,
        file_id: str,
        destination: str | Path | None = None,
        *,
        export_format: str | None = None,
    ) -> DownloadResult:
        """Download a Drive file (or export a Google-native doc).

        Args:
            file_id: Drive file id.
            destination: Local path. If omitted, uses the Drive file name in CWD.
            export_format: Required for Docs/Sheets/Slides natives (e.g. ``pdf``, ``docx``).
        """
        if destination is None:
            meta = self.files.get(file_id)
            destination = Path.cwd() / meta.name
        return self.files.download_path(
            file_id,
            destination,
            export_format=export_format,
        )

    def upload_folder(
        self: DriveClient,
        local_path: str | Path,
        *,
        parent_id: str | None = None,
        overwrite: OverwritePolicy | str = OverwritePolicy.ERROR,
        progress: ProgressCallback | None = None,
    ) -> DriveFolder:
        """Recursively upload a local directory into Drive.

        Args:
            local_path: Local directory path.
            parent_id: Destination parent folder id (root if omitted).
            overwrite: Conflict policy for existing names.
            progress: Optional per-file progress callback.
        """
        return self.folders.upload_directory(
            local_path,
            parent_id=parent_id,
            overwrite=overwrite,
            progress=progress,
        )

    def delete_file(
        self: DriveClient,
        file_id: str,
        *,
        permanently: bool = False,
    ) -> DriveFile | None:
        """Trash a file, or permanently delete when ``permanently=True``.

        Args:
            file_id: Drive file id.
            permanently: If True, permanently delete; otherwise trash.

        Returns:
            Trashed :class:`~googlekit.gdrive.models.DriveFile`, or ``None`` if permanently deleted.
        """
        if permanently:
            self.files.delete(file_id)
            return None
        return self.files.trash(file_id)

    def delete_folder(
        self: DriveClient,
        folder_id: str,
        *,
        permanently: bool = False,
    ) -> DriveFile | None:
        """Trash a folder, or permanently delete when ``permanently=True``.

        Args:
            folder_id: Drive folder id.
            permanently: If True, permanently delete; otherwise trash.
        """
        return self.delete_file(folder_id, permanently=permanently)

    def share(
        self: DriveClient,
        file_id: str,
        *,
        email: str | None = None,
        public: bool = False,
        role: PermissionRole | str = PermissionRole.READER,
        notify: bool = True,
    ) -> Permission:
        """Share with a user email, or make link public (requires ``public=True``).

        Args:
            file_id: File or folder id.
            email: Google account to share with (writer/reader/…).
            public: If True, creates an anyone-with-link permission (explicit guard).
            role: Permission role (default reader).
            notify: Email the user when sharing by ``email``.
        """
        if public:
            return self.permissions.share_anyone(file_id, role=role, public=True)
        if email:
            return self.permissions.share_user(
                file_id, email, role=role, notify=notify
            )
        raise ValidationError("share requires email=... and/or public=True")

    def unshare(
        self: DriveClient,
        file_id: str,
        *,
        email: str | None = None,
        remove_public: bool = False,
    ) -> int:
        """Remove sharing for an email and/or public (anyone) link.

        Args:
            file_id: File or folder id.
            email: Remove permissions for this email (case-insensitive).
            remove_public: Also remove ``anyone`` (link) permissions.

        Returns:
            Number of permissions removed.
        """
        if not email and not remove_public:
            raise ValidationError("unshare requires email=... and/or remove_public=True")
        removed = 0
        for perm in self.permissions.list(file_id):
            if email and perm.email_address and perm.email_address.lower() == email.lower():
                self.permissions.remove(file_id, perm.id)
                removed += 1
            elif remove_public and perm.type == "anyone":
                self.permissions.remove(file_id, perm.id)
                removed += 1
        return removed

    def list_permissions(self: DriveClient, file_id: str) -> list[Permission]:
        """List who has access to a file or folder.

        Args:
            file_id: File or folder id.
        """
        return self.permissions.list(file_id)

    def get_share_link(
        self: DriveClient,
        file_id: str,
        *,
        role: PermissionRole | str = PermissionRole.READER,
        public: bool = True,
    ) -> str:
        """Return a shareable web link (creates anyone permission when ``public=True``).

        Args:
            file_id: File or folder id.
            role: Role for the anyone link (default reader).
            public: Must be True to create/ensure anyone-with-link access.
        """
        return self.permissions.create_shareable_link(
            file_id, role=role, public=public
        )
