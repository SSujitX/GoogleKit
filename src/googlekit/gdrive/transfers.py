"""Resumable upload/download and Google-native export helpers."""

from __future__ import annotations

import io
import logging
import mimetypes
from collections.abc import Callable
from pathlib import Path
from typing import Any, BinaryIO

from googlekit.core.constants import DEFAULT_CHUNK_SIZE
from googlekit.core.exceptions import ValidationError
from googlekit.core.transport import Transport
from googlekit.core.validation import require_non_empty, require_path, require_positive_int
from googlekit.gdrive.export_formats import EXPORT_MIME_MAP, resolve_export_mime
from googlekit.gdrive.models import (
    FILE_FIELDS,
    DownloadResult,
    DriveFile,
    UploadResult,
    shared_drive_params,
)

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int | None], None]

__all__ = [
    "EXPORT_MIME_MAP",
    "DriveTransfers",
    "ProgressCallback",
    "guess_mime_type",
    "resolve_export_mime",
]


def guess_mime_type(path: Path) -> str:
    """Guess a MIME type from a local path."""
    guessed, _ = mimetypes.guess_type(str(path))
    return guessed or "application/octet-stream"


class DriveTransfers:
    """Low-level media transfer operations against Drive API v3."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    @property
    def _supports_all(self) -> bool:
        return self._transport.config.supports_all_drives

    def _service(self) -> Any:
        return self._transport.get_service("drive", "v3")

    def _chunk_size(self, chunk_size: int | None) -> int:
        size = chunk_size if chunk_size is not None else self._transport.config.chunk_size
        return require_positive_int(size, "chunk_size")

    def upload_path(
        self,
        path: str | Path,
        *,
        name: str | None = None,
        parents: list[str] | None = None,
        mime_type: str | None = None,
        file_id: str | None = None,
        chunk_size: int | None = None,
        progress: ProgressCallback | None = None,
        resumable: bool = True,
        fields: str = FILE_FIELDS,
    ) -> UploadResult:
        """Upload a local file path using resumable or multipart upload."""
        local = require_path(path, must_exist=True)
        if not local.is_file():
            raise ValidationError(f"Not a file: {local}")
        from googleapiclient.http import MediaFileUpload

        media = MediaFileUpload(
            str(local),
            mimetype=mime_type or guess_mime_type(local),
            resumable=resumable,
            chunksize=self._chunk_size(chunk_size),
        )
        body: dict[str, Any] = {"name": name or local.name}
        if parents and not file_id:
            body["parents"] = parents
        return self._run_upload(
            media,
            body=body,
            file_id=file_id,
            progress=progress,
            fields=fields,
            bytes_hint=local.stat().st_size,
        )

    def upload_bytes(
        self,
        data: bytes,
        *,
        name: str,
        parents: list[str] | None = None,
        mime_type: str = "application/octet-stream",
        file_id: str | None = None,
        chunk_size: int | None = None,
        progress: ProgressCallback | None = None,
        resumable: bool | None = None,
        fields: str = FILE_FIELDS,
    ) -> UploadResult:
        """Upload from an in-memory bytes buffer."""
        require_non_empty(name, "name")
        use_resumable = resumable if resumable is not None else len(data) > DEFAULT_CHUNK_SIZE
        buffer = io.BytesIO(data)
        return self.upload_fileobj(
            buffer,
            name=name,
            parents=parents,
            mime_type=mime_type,
            file_id=file_id,
            chunk_size=chunk_size,
            progress=progress,
            resumable=use_resumable,
            size=len(data),
            fields=fields,
        )

    def upload_fileobj(
        self,
        fileobj: BinaryIO,
        *,
        name: str,
        parents: list[str] | None = None,
        mime_type: str = "application/octet-stream",
        file_id: str | None = None,
        chunk_size: int | None = None,
        progress: ProgressCallback | None = None,
        resumable: bool = True,
        size: int | None = None,
        fields: str = FILE_FIELDS,
    ) -> UploadResult:
        """Upload from a binary file-like object."""
        require_non_empty(name, "name")
        from googleapiclient.http import MediaIoBaseUpload

        media = MediaIoBaseUpload(
            fileobj,
            mimetype=mime_type,
            resumable=resumable,
            chunksize=self._chunk_size(chunk_size),
        )
        body: dict[str, Any] = {"name": name}
        if parents and not file_id:
            body["parents"] = parents
        return self._run_upload(
            media,
            body=body,
            file_id=file_id,
            progress=progress,
            fields=fields,
            bytes_hint=size,
        )

    def _run_upload(
        self,
        media: Any,
        *,
        body: dict[str, Any],
        file_id: str | None,
        progress: ProgressCallback | None,
        fields: str,
        bytes_hint: int | None,
    ) -> UploadResult:
        service = self._service()
        sd = shared_drive_params(self._supports_all)
        if file_id:
            request = service.files().update(
                fileId=file_id,
                body=body,
                media_body=media,
                fields=fields,
                **sd,
            )
        else:
            request = service.files().create(
                body=body,
                media_body=media,
                fields=fields,
                **sd,
            )
        response = self._execute_media(request, progress=progress, total_hint=bytes_hint)
        drive_file = DriveFile.from_api(response)
        return UploadResult(
            file=drive_file,
            bytes_uploaded=bytes_hint if bytes_hint is not None else drive_file.size,
            overwritten=file_id is not None,
            raw=response,
        )

    def download_path(
        self,
        file_id: str,
        destination: str | Path,
        *,
        chunk_size: int | None = None,
        progress: ProgressCallback | None = None,
        export_mime: str | None = None,
    ) -> DownloadResult:
        """Download or export a file directly to a path without buffering all bytes."""
        require_non_empty(file_id, "file_id")
        dest = Path(destination)
        dest.parent.mkdir(parents=True, exist_ok=True)
        service = self._service()
        request = self._media_request(service, file_id, export_mime=export_mime)
        from googleapiclient.http import MediaIoBaseDownload

        with dest.open("wb") as handle:
            downloader = MediaIoBaseDownload(
                handle,
                request,
                chunksize=self._chunk_size(chunk_size),
            )
            size = self._consume_download(downloader, progress=progress)
        return DownloadResult(
            path=dest,
            size=size,
            mime_type=export_mime,
            exported=export_mime is not None,
        )

    def download_bytes(
        self,
        file_id: str,
        *,
        chunk_size: int | None = None,
        progress: ProgressCallback | None = None,
        export_mime: str | None = None,
    ) -> DownloadResult:
        """Download or export a file into memory (explicit bytes request)."""
        require_non_empty(file_id, "file_id")
        buffer = io.BytesIO()
        result = self.download_fileobj(
            file_id,
            buffer,
            chunk_size=chunk_size,
            progress=progress,
            export_mime=export_mime,
        )
        data = buffer.getvalue()
        return DownloadResult(
            size=len(data),
            mime_type=export_mime or result.mime_type,
            exported=export_mime is not None,
            data=data,
        )

    def download_fileobj(
        self,
        file_id: str,
        fileobj: BinaryIO,
        *,
        chunk_size: int | None = None,
        progress: ProgressCallback | None = None,
        export_mime: str | None = None,
    ) -> DownloadResult:
        """Download or export into a binary file-like object."""
        require_non_empty(file_id, "file_id")
        service = self._service()
        request = self._media_request(service, file_id, export_mime=export_mime)
        from googleapiclient.http import MediaIoBaseDownload

        downloader = MediaIoBaseDownload(
            fileobj,
            request,
            chunksize=self._chunk_size(chunk_size),
        )
        size = self._consume_download(downloader, progress=progress)
        return DownloadResult(
            size=size,
            mime_type=export_mime,
            exported=export_mime is not None,
        )

    def _media_request(
        self,
        service: Any,
        file_id: str,
        *,
        export_mime: str | None,
    ) -> Any:
        sd = shared_drive_params(self._supports_all)
        if export_mime:
            return service.files().export_media(fileId=file_id, mimeType=export_mime)
        return service.files().get_media(fileId=file_id, **sd)

    def _execute_media(
        self,
        request: Any,
        *,
        progress: ProgressCallback | None,
        total_hint: int | None,
    ) -> dict[str, Any]:
        if getattr(request, "resumable", None) is None:
            return self._transport.execute(request)

        from googlekit.core.transport import map_http_error

        response: dict[str, Any] | None = None
        while response is None:
            try:
                status, response = request.next_chunk()
            except Exception as exc:
                name = type(exc).__name__
                if name == "HttpError" or hasattr(exc, "resp"):
                    raise map_http_error(exc) from exc
                raise
            if progress and status is not None:
                try:
                    progress(int(status.resumable_progress), total_hint)
                except Exception:  # pragma: no cover
                    logger.debug("Upload progress callback failed", exc_info=True)
        return response

    def _consume_download(
        self,
        downloader: Any,
        *,
        progress: ProgressCallback | None,
    ) -> int:
        from googlekit.core.transport import map_http_error

        done = False
        size = 0
        while not done:
            try:
                status, done = downloader.next_chunk()
            except Exception as exc:
                name = type(exc).__name__
                if name == "HttpError" or hasattr(exc, "resp"):
                    raise map_http_error(exc) from exc
                raise
            if status is not None:
                size = int(status.resumable_progress)
                if progress:
                    total = None
                    try:
                        total = int(status.total_size) if status.total_size else None
                    except Exception:  # pragma: no cover
                        total = None
                    try:
                        progress(size, total)
                    except Exception:  # pragma: no cover
                        logger.debug("Download progress callback failed", exc_info=True)
        return size
