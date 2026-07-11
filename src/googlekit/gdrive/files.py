"""Google Drive file operations manager."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from googlekit.core.constants import DEFAULT_PAGE_SIZE, DRIVE_FOLDER_MIME
from googlekit.core.exceptions import ValidationError
from googlekit.core.pagination import Page, PageIterator
from googlekit.core.transport import Transport
from googlekit.core.validation import require_non_empty
from googlekit.gdrive.file_media import FileMediaMixin
from googlekit.gdrive.models import (
    FILE_FIELDS,
    DriveFile,
    shared_drive_params,
)
from googlekit.gdrive.transfers import DriveTransfers


class FilesManager(FileMediaMixin):
    """Manage Drive files: list, search, upload, download, metadata, trash."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport
        self._transfers = DriveTransfers(transport)

    def _service(self) -> Any:
        return self._transport.get_service("drive", "v3")

    @property
    def _sd(self) -> dict[str, bool]:
        return shared_drive_params(self._transport.config.supports_all_drives)

    @property
    def _sd_list(self) -> dict[str, bool]:
        return shared_drive_params(
            self._transport.config.supports_all_drives,
            list_mode=True,
        )

    def list(
        self,
        *,
        query: str | None = None,
        folder_id: str | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
        page_token: str | None = None,
        order_by: str | None = None,
        fields: str = FILE_FIELDS,
        corpora: str | None = None,
        drive_id: str | None = None,
        include_trashed: bool = False,
    ) -> Page[DriveFile]:
        """Return one page of files matching optional filters."""
        q = self._build_query(query, folder_id=folder_id, include_trashed=include_trashed)
        return self._fetch_page(
            q,
            page_size=page_size,
            page_token=page_token,
            order_by=order_by,
            fields=fields,
            corpora=corpora,
            drive_id=drive_id,
        )

    def iterate(
        self,
        *,
        query: str | None = None,
        folder_id: str | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
        page_token: str | None = None,
        order_by: str | None = None,
        fields: str = FILE_FIELDS,
        corpora: str | None = None,
        drive_id: str | None = None,
        include_trashed: bool = False,
    ) -> PageIterator[DriveFile]:
        """Lazily iterate all matching files across pages."""
        q = self._build_query(query, folder_id=folder_id, include_trashed=include_trashed)

        def fetch(token: str | None, size: int) -> Page[DriveFile]:
            return self._fetch_page(
                q,
                page_size=size,
                page_token=token,
                order_by=order_by,
                fields=fields,
                corpora=corpora,
                drive_id=drive_id,
            )

        return PageIterator(fetch, page_size=page_size, page_token=page_token)

    def search(
        self,
        query: str,
        *,
        page_size: int = DEFAULT_PAGE_SIZE,
        page_token: str | None = None,
        order_by: str | None = None,
        fields: str = FILE_FIELDS,
        corpora: str | None = None,
        drive_id: str | None = None,
    ) -> Page[DriveFile]:
        """Search using Drive query syntax (e.g. ``name contains 'report'``)."""
        require_non_empty(query, "query")
        return self.list(
            query=query,
            page_size=page_size,
            page_token=page_token,
            order_by=order_by,
            fields=fields,
            corpora=corpora,
            drive_id=drive_id,
        )

    def get(self, file_id: str, *, fields: str = FILE_FIELDS) -> DriveFile:
        """Fetch metadata for a single file."""
        require_non_empty(file_id, "file_id")
        response = self._transport.execute(
            self._service().files().get(fileId=file_id, fields=fields, **self._sd)
        )
        return DriveFile.from_api(response)

    def create(
        self,
        name: str,
        *,
        mime_type: str = "application/octet-stream",
        parents: list[str] | None = None,
        fields: str = FILE_FIELDS,
        **metadata: Any,
    ) -> DriveFile:
        """Create a file metadata entry (optionally empty / Google-native)."""
        require_non_empty(name, "name")
        body: dict[str, Any] = {"name": name, "mimeType": mime_type, **metadata}
        if parents:
            body["parents"] = parents
        response = self._transport.execute(
            self._service().files().create(body=body, fields=fields, **self._sd)
        )
        return DriveFile.from_api(response)

    def copy(
        self,
        file_id: str,
        *,
        name: str | None = None,
        parents: list[str] | None = None,
        fields: str = FILE_FIELDS,
    ) -> DriveFile:
        """Copy a file, optionally renaming or re-parenting."""
        require_non_empty(file_id, "file_id")
        body: dict[str, Any] = {}
        if name:
            body["name"] = name
        if parents is not None:
            body["parents"] = parents
        response = self._transport.execute(
            self._service()
            .files()
            .copy(
                fileId=file_id,
                body=body,
                fields=fields,
                **self._sd,
            )
        )
        return DriveFile.from_api(response)

    def move(
        self,
        file_id: str,
        *,
        add_parents: list[str] | None = None,
        remove_parents: list[str] | None = None,
        fields: str = FILE_FIELDS,
    ) -> DriveFile:
        """Move a file by adding/removing parents."""
        require_non_empty(file_id, "file_id")
        if not add_parents and not remove_parents:
            raise ValidationError("move requires add_parents and/or remove_parents")
        kwargs: dict[str, Any] = {"fileId": file_id, "fields": fields, **self._sd}
        if add_parents:
            kwargs["addParents"] = ",".join(add_parents)
        if remove_parents:
            kwargs["removeParents"] = ",".join(remove_parents)
        response = self._transport.execute(self._service().files().update(**kwargs))
        return DriveFile.from_api(response)

    def rename(self, file_id: str, name: str, *, fields: str = FILE_FIELDS) -> DriveFile:
        """Rename a file."""
        return self.update_metadata(file_id, name=name, fields=fields)

    def update_metadata(
        self,
        file_id: str,
        *,
        fields: str = FILE_FIELDS,
        **metadata: Any,
    ) -> DriveFile:
        """Patch file metadata fields."""
        require_non_empty(file_id, "file_id")
        if not metadata:
            raise ValidationError("update_metadata requires at least one field")
        body = _normalize_metadata(metadata)
        response = self._transport.execute(
            self._service()
            .files()
            .update(
                fileId=file_id,
                body=body,
                fields=fields,
                **self._sd,
            )
        )
        return DriveFile.from_api(response)

    def trash(self, file_id: str, *, fields: str = FILE_FIELDS) -> DriveFile:
        """Move a file to trash."""
        return self.update_metadata(file_id, trashed=True, fields=fields)

    def restore(self, file_id: str, *, fields: str = FILE_FIELDS) -> DriveFile:
        """Restore a file from trash."""
        return self.update_metadata(file_id, trashed=False, fields=fields)

    def delete(self, file_id: str) -> None:
        """Permanently delete a file (cannot be undone)."""
        require_non_empty(file_id, "file_id")
        self._transport.execute(self._service().files().delete(fileId=file_id, **self._sd))

    def find_by_name(
        self,
        name: str,
        *,
        parents: list[str] | None = None,
        mime_type: str | None = None,
    ) -> DriveFile | None:
        """Return the first non-trashed file with an exact name under parents."""
        require_non_empty(name, "name")
        parts = [f"name = '{_escape_query(name)}'", "trashed = false"]
        if parents:
            parent_q = " or ".join(f"'{p}' in parents" for p in parents)
            parts.append(f"({parent_q})")
        if mime_type:
            parts.append(f"mimeType = '{mime_type}'")
        page = self.search(" and ".join(parts), page_size=1)
        return page.items[0] if page.items else None

    def _build_query(
        self,
        query: str | None,
        *,
        folder_id: str | None,
        include_trashed: bool,
    ) -> str | None:
        parts: list[str] = []
        if query:
            parts.append(f"({query})")
        if folder_id:
            parts.append(f"'{folder_id}' in parents")
        if not include_trashed:
            parts.append("trashed = false")
        return " and ".join(parts) if parts else None

    def _fetch_page(
        self,
        query: str | None,
        *,
        page_size: int,
        page_token: str | None,
        order_by: str | None,
        fields: str,
        corpora: str | None,
        drive_id: str | None,
    ) -> Page[DriveFile]:
        kwargs: dict[str, Any] = {
            "pageSize": page_size,
            "fields": f"nextPageToken, files({fields})",
            **self._sd_list,
        }
        if query:
            kwargs["q"] = query
        if page_token:
            kwargs["pageToken"] = page_token
        if order_by:
            kwargs["orderBy"] = order_by
        if corpora:
            kwargs["corpora"] = corpora
        if drive_id:
            kwargs["driveId"] = drive_id
        response = self._transport.execute(self._service().files().list(**kwargs))
        items = [DriveFile.from_api(f) for f in response.get("files", [])]
        return Page(
            items=items,
            next_page_token=response.get("nextPageToken"),
            raw=response,
        )


def _escape_query(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _normalize_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    mapping = {
        "mime_type": "mimeType",
        "web_view_link": "webViewLink",
        "web_content_link": "webContentLink",
        "created_time": "createdTime",
        "modified_time": "modifiedTime",
        "drive_id": "driveId",
        "md5_checksum": "md5Checksum",
    }
    body: dict[str, Any] = {}
    for key, value in metadata.items():
        body[mapping.get(key, key)] = value
    return body


def iter_non_folder_children(
    files: FilesManager,
    folder_id: str,
) -> Iterator[DriveFile]:
    """Iterate non-folder children of a folder."""
    query = f"mimeType != '{DRIVE_FOLDER_MIME}'"
    yield from files.iterate(query=query, folder_id=folder_id)
