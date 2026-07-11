"""Media upload/download methods mixed into FilesManager."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO

from googlekit.core.exceptions import ValidationError
from googlekit.core.validation import require_path
from googlekit.gdrive.export_formats import resolve_export_mime
from googlekit.gdrive.models import DownloadResult, OverwritePolicy, UploadResult
from googlekit.gdrive.transfers import DriveTransfers, ProgressCallback

if TYPE_CHECKING:
    from googlekit.gdrive.files import FilesManager

logger = logging.getLogger(__name__)


class FileMediaMixin:
    """Upload/download/export operations for :class:`FilesManager`."""

    _transfers: DriveTransfers

    def upload_path(
        self: FilesManager,
        path: str | Path,
        *,
        parents: list[str] | None = None,
        name: str | None = None,
        mime_type: str | None = None,
        overwrite: OverwritePolicy | str = OverwritePolicy.ERROR,
        chunk_size: int | None = None,
        progress: ProgressCallback | None = None,
        resumable: bool = True,
    ) -> UploadResult | None:
        """Upload a local file path into Drive."""
        local = require_path(path, must_exist=True)
        file_name = name or local.name
        existing = self._resolve_overwrite(
            file_name,
            parents=parents,
            overwrite=OverwritePolicy(overwrite),
        )
        if existing is False:
            return None
        return self._transfers.upload_path(
            local,
            name=file_name,
            parents=parents,
            mime_type=mime_type,
            file_id=existing,
            chunk_size=chunk_size,
            progress=progress,
            resumable=resumable,
        )

    def upload_bytes(
        self: FilesManager,
        data: bytes,
        name: str,
        *,
        parents: list[str] | None = None,
        mime_type: str = "application/octet-stream",
        overwrite: OverwritePolicy | str = OverwritePolicy.ERROR,
        chunk_size: int | None = None,
        progress: ProgressCallback | None = None,
    ) -> UploadResult | None:
        """Upload bytes as a new (or overwritten) Drive file."""
        existing = self._resolve_overwrite(
            name,
            parents=parents,
            overwrite=OverwritePolicy(overwrite),
        )
        if existing is False:
            return None
        return self._transfers.upload_bytes(
            data,
            name=name,
            parents=parents,
            mime_type=mime_type,
            file_id=existing,
            chunk_size=chunk_size,
            progress=progress,
        )

    def upload_fileobj(
        self: FilesManager,
        fileobj: BinaryIO,
        name: str,
        *,
        parents: list[str] | None = None,
        mime_type: str = "application/octet-stream",
        overwrite: OverwritePolicy | str = OverwritePolicy.ERROR,
        chunk_size: int | None = None,
        progress: ProgressCallback | None = None,
        size: int | None = None,
        resumable: bool = True,
    ) -> UploadResult | None:
        """Upload from a binary file-like object."""
        existing = self._resolve_overwrite(
            name,
            parents=parents,
            overwrite=OverwritePolicy(overwrite),
        )
        if existing is False:
            return None
        return self._transfers.upload_fileobj(
            fileobj,
            name=name,
            parents=parents,
            mime_type=mime_type,
            file_id=existing,
            chunk_size=chunk_size,
            progress=progress,
            size=size,
            resumable=resumable,
        )

    def download_path(
        self: FilesManager,
        file_id: str,
        destination: str | Path,
        *,
        chunk_size: int | None = None,
        progress: ProgressCallback | None = None,
        export_format: str | None = None,
    ) -> DownloadResult:
        """Download a binary file (or export a Google-native file) to a path."""
        export_mime = self._export_mime_for(file_id, export_format)
        return self._transfers.download_path(
            file_id,
            destination,
            chunk_size=chunk_size,
            progress=progress,
            export_mime=export_mime,
        )

    def download_bytes(
        self: FilesManager,
        file_id: str,
        *,
        chunk_size: int | None = None,
        progress: ProgressCallback | None = None,
        export_format: str | None = None,
    ) -> DownloadResult:
        """Download into memory. Prefer ``download_path`` for large files."""
        export_mime = self._export_mime_for(file_id, export_format)
        return self._transfers.download_bytes(
            file_id,
            chunk_size=chunk_size,
            progress=progress,
            export_mime=export_mime,
        )

    def download_fileobj(
        self: FilesManager,
        file_id: str,
        fileobj: BinaryIO,
        *,
        chunk_size: int | None = None,
        progress: ProgressCallback | None = None,
        export_format: str | None = None,
    ) -> DownloadResult:
        """Download into a binary file-like object."""
        export_mime = self._export_mime_for(file_id, export_format)
        return self._transfers.download_fileobj(
            file_id,
            fileobj,
            chunk_size=chunk_size,
            progress=progress,
            export_mime=export_mime,
        )

    def export(
        self: FilesManager,
        file_id: str,
        export_format: str,
        destination: str | Path | None = None,
        *,
        chunk_size: int | None = None,
        progress: ProgressCallback | None = None,
    ) -> DownloadResult:
        """Export a Google-native file to ``export_format`` (short name or MIME)."""
        meta = self.get(file_id, fields="id,name,mimeType")
        if not meta.mime_type:
            raise ValidationError(f"File {file_id!r} has no MIME type")
        mime = resolve_export_mime(meta.mime_type, export_format)
        if destination is None:
            return self._transfers.download_bytes(
                file_id,
                chunk_size=chunk_size,
                progress=progress,
                export_mime=mime,
            )
        return self._transfers.download_path(
            file_id,
            destination,
            chunk_size=chunk_size,
            progress=progress,
            export_mime=mime,
        )

    def _export_mime_for(
        self: FilesManager,
        file_id: str,
        export_format: str | None,
    ) -> str | None:
        if export_format is None:
            meta = self.get(file_id, fields="id,mimeType")
            if meta.is_google_native:
                raise ValidationError(
                    f"File {file_id!r} is Google-native ({meta.mime_type}). "
                    "Use export() or pass export_format=..."
                )
            return None
        meta = self.get(file_id, fields="id,mimeType")
        if not meta.mime_type:
            raise ValidationError(f"File {file_id!r} has no MIME type")
        return resolve_export_mime(meta.mime_type, export_format)

    def _resolve_overwrite(
        self: FilesManager,
        name: str,
        *,
        parents: list[str] | None,
        overwrite: OverwritePolicy,
    ) -> str | None | bool:
        """Return existing file id, None for create, or False when skipping."""
        search_parents = parents if parents is not None else ["root"]
        existing = self.find_by_name(name, parents=search_parents)
        if existing is None:
            return None
        if overwrite is OverwritePolicy.SKIP:
            logger.info("Skipping upload; %r already exists as %s", name, existing.id)
            return False
        if overwrite is OverwritePolicy.ERROR:
            raise ValidationError(
                f"A file named {name!r} already exists (id={existing.id}). "
                "Pass overwrite=OverwritePolicy.OVERWRITE or SKIP."
            )
        return existing.id
