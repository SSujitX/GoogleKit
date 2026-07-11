"""Google Drive changes feed manager."""

from __future__ import annotations

from typing import Any

from googlekit.core.constants import DEFAULT_PAGE_SIZE
from googlekit.core.pagination import Page, PageIterator
from googlekit.core.transport import Transport
from googlekit.core.validation import require_non_empty
from googlekit.gdrive.models import CHANGE_FIELDS, Change, shared_drive_params


class ChangesManager:
    """Access the Drive changes feed for incremental sync."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def _service(self) -> Any:
        return self._transport.get_service("drive", "v3")

    @property
    def _sd(self) -> dict[str, bool]:
        """Params for getStartPageToken (supportsAllDrives only)."""
        return shared_drive_params(self._transport.config.supports_all_drives)

    @property
    def _sd_list(self) -> dict[str, bool]:
        """Params for changes.list (includes includeItemsFromAllDrives)."""
        return shared_drive_params(
            self._transport.config.supports_all_drives,
            list_mode=True,
        )

    def get_start_page_token(self, *, drive_id: str | None = None) -> str:
        """Return a page token for future ``list`` / ``iterate`` calls.

        Official ``changes.getStartPageToken`` accepts ``driveId`` and
        ``supportsAllDrives`` only — not ``includeItemsFromAllDrives``.
        """
        kwargs: dict[str, Any] = {**self._sd}
        if drive_id:
            kwargs["driveId"] = drive_id
        response = self._transport.execute(self._service().changes().getStartPageToken(**kwargs))
        token = response.get("startPageToken")
        if not token:
            raise RuntimeError("Drive API returned no startPageToken")
        return str(token)

    def list(
        self,
        page_token: str,
        *,
        page_size: int = DEFAULT_PAGE_SIZE,
        drive_id: str | None = None,
        include_removed: bool = True,
        fields: str = CHANGE_FIELDS,
    ) -> Page[Change]:
        """Return one page of changes starting at ``page_token``."""
        require_non_empty(page_token, "page_token")
        return self._fetch_page(
            page_token,
            page_size=page_size,
            drive_id=drive_id,
            include_removed=include_removed,
            fields=fields,
        )

    def iterate(
        self,
        page_token: str,
        *,
        page_size: int = DEFAULT_PAGE_SIZE,
        drive_id: str | None = None,
        include_removed: bool = True,
        fields: str = CHANGE_FIELDS,
    ) -> PageIterator[Change]:
        """Lazily iterate changes from ``page_token`` until exhausted."""
        require_non_empty(page_token, "page_token")

        def fetch(token: str | None, size: int) -> Page[Change]:
            if not token:
                return Page(items=[], next_page_token=None)
            return self._fetch_page(
                token,
                page_size=size,
                drive_id=drive_id,
                include_removed=include_removed,
                fields=fields,
            )

        return PageIterator(fetch, page_size=page_size, page_token=page_token)

    def _fetch_page(
        self,
        page_token: str,
        *,
        page_size: int,
        drive_id: str | None,
        include_removed: bool,
        fields: str,
    ) -> Page[Change]:
        kwargs: dict[str, Any] = {
            "pageToken": page_token,
            "pageSize": page_size,
            "includeRemoved": include_removed,
            "fields": fields,
            **self._sd_list,
        }
        if drive_id:
            kwargs["driveId"] = drive_id
        response = self._transport.execute(self._service().changes().list(**kwargs))
        items = [Change.from_api(c) for c in response.get("changes", [])]
        next_token = response.get("nextPageToken") or response.get("newStartPageToken")
        # newStartPageToken means the feed is caught up; stop iteration.
        if not response.get("nextPageToken") and response.get("newStartPageToken"):
            next_token = None
        return Page(items=items, next_page_token=next_token, raw=response)
