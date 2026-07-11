"""Spreadsheets manager — create, get, title, batchUpdate."""

from __future__ import annotations

from typing import Any

from googlekit.core.exceptions import ValidationError
from googlekit.core.transport import Transport
from googlekit.core.types import SpreadsheetId
from googlekit.core.validation import require_non_empty
from googlekit.gsheets.models import BatchUpdateResponse, Spreadsheet


class SpreadsheetsManager:
    """Operations on spreadsheet resources (Sheets API v4)."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def _service(self) -> Any:
        return self._transport.get_service("sheets", "v4")

    def create(
        self,
        title: str = "Untitled spreadsheet",
        *,
        locale: str | None = None,
        time_zone: str | None = None,
        sheet_count: int = 1,
    ) -> Spreadsheet:
        """Create a new spreadsheet.

        Args:
            title: Spreadsheet title.
            locale: Optional locale (e.g. ``en_US``).
            time_zone: Optional IANA time zone.
            sheet_count: Number of initial worksheets (minimum 1).

        Returns:
            The created :class:`Spreadsheet`.
        """
        require_non_empty(title, "title")
        if sheet_count < 1:
            raise ValidationError("sheet_count must be >= 1")
        props: dict[str, Any] = {"title": title}
        if locale:
            props["locale"] = locale
        if time_zone:
            props["timeZone"] = time_zone
        body: dict[str, Any] = {
            "properties": props,
            "sheets": [
                {"properties": {"title": "Sheet1" if i == 0 else f"Sheet{i + 1}"}}
                for i in range(sheet_count)
            ],
        }
        request = self._service().spreadsheets().create(body=body)
        data = self._transport.execute(request)
        return Spreadsheet.from_api(data)

    def get(
        self,
        spreadsheet_id: SpreadsheetId,
        *,
        ranges: list[str] | None = None,
        include_grid_data: bool = False,
    ) -> Spreadsheet:
        """Fetch spreadsheet metadata (and optionally grid data).

        Args:
            spreadsheet_id: Spreadsheet ID.
            ranges: Optional A1 ranges to limit returned sheets/data.
            include_grid_data: When True, include cell data (expensive).

        Returns:
            Spreadsheet metadata.
        """
        sid = require_non_empty(spreadsheet_id, "spreadsheet_id")
        kwargs: dict[str, Any] = {
            "spreadsheetId": sid,
            "includeGridData": include_grid_data,
        }
        if ranges:
            kwargs["ranges"] = ranges
        request = self._service().spreadsheets().get(**kwargs)
        data = self._transport.execute(request)
        return Spreadsheet.from_api(data)

    def set_title(self, spreadsheet_id: SpreadsheetId, title: str) -> Spreadsheet:
        """Rename a spreadsheet.

        Args:
            spreadsheet_id: Spreadsheet ID.
            title: New title.

        Returns:
            Updated spreadsheet metadata.
        """
        sid = require_non_empty(spreadsheet_id, "spreadsheet_id")
        require_non_empty(title, "title")
        self.batch_update(
            sid,
            [{"updateSpreadsheetProperties": {"properties": {"title": title}, "fields": "title"}}],
        )
        return self.get(sid)

    def batch_update(
        self,
        spreadsheet_id: SpreadsheetId,
        requests: list[dict[str, Any]],
        *,
        include_spreadsheet_in_response: bool = False,
        response_ranges: list[str] | None = None,
        response_include_grid_data: bool = False,
    ) -> BatchUpdateResponse:
        """Execute one or more batchUpdate requests.

        Args:
            spreadsheet_id: Spreadsheet ID.
            requests: Sheets API request objects.
            include_spreadsheet_in_response: Include full spreadsheet in reply.
            response_ranges: Optional ranges when including spreadsheet.
            response_include_grid_data: Include grid data in response spreadsheet.

        Returns:
            Batch update response with replies.
        """
        sid = require_non_empty(spreadsheet_id, "spreadsheet_id")
        if not requests:
            raise ValidationError("requests must be a non-empty list")
        body: dict[str, Any] = {
            "requests": requests,
            "includeSpreadsheetInResponse": include_spreadsheet_in_response,
            "responseIncludeGridData": response_include_grid_data,
        }
        if response_ranges:
            body["responseRanges"] = response_ranges
        request = self._service().spreadsheets().batchUpdate(spreadsheetId=sid, body=body)
        data = self._transport.execute(request)
        return BatchUpdateResponse.from_api(data)
