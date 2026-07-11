"""Worksheets manager — create, rename, delete, resize, freeze, hide."""

from __future__ import annotations

from typing import Any

from googlekit.core.exceptions import NotFoundError, ValidationError
from googlekit.core.transport import Transport
from googlekit.core.types import SpreadsheetId
from googlekit.core.validation import require_non_empty, require_positive_int
from googlekit.gsheets.models import BatchUpdateResponse, Spreadsheet, Worksheet
from googlekit.gsheets.spreadsheets import SpreadsheetsManager


class WorksheetsManager:
    """Manage individual sheets (tabs) within a spreadsheet."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport
        self._spreadsheets = SpreadsheetsManager(transport)

    def list(self, spreadsheet_id: SpreadsheetId) -> list[Worksheet]:
        """List all worksheets in a spreadsheet."""
        return self._spreadsheets.get(spreadsheet_id).worksheets

    def create(
        self,
        spreadsheet_id: SpreadsheetId,
        title: str,
        *,
        rows: int = 1000,
        columns: int = 26,
        index: int | None = None,
    ) -> Worksheet:
        """Add a new worksheet and return its properties."""
        require_non_empty(title, "title")
        require_positive_int(rows, "rows")
        require_positive_int(columns, "columns")
        props: dict[str, Any] = {
            "title": title,
            "gridProperties": {"rowCount": rows, "columnCount": columns},
        }
        if index is not None:
            if index < 0:
                raise ValidationError("index must be >= 0")
            props["index"] = index
        resp = self._spreadsheets.batch_update(
            spreadsheet_id,
            [{"addSheet": {"properties": props}}],
        )
        reply = (resp.replies or [{}])[0]
        added = (reply.get("addSheet") or {}).get("properties") or {}
        sheet = Worksheet.from_api({"properties": added})
        return sheet

    def rename(
        self,
        spreadsheet_id: SpreadsheetId,
        sheet_id: int,
        title: str,
    ) -> BatchUpdateResponse:
        """Rename a worksheet by sheet ID."""
        require_non_empty(title, "title")
        return self._spreadsheets.batch_update(
            spreadsheet_id,
            [
                {
                    "updateSheetProperties": {
                        "properties": {"sheetId": sheet_id, "title": title},
                        "fields": "title",
                    }
                }
            ],
        )

    def delete(self, spreadsheet_id: SpreadsheetId, sheet_id: int) -> BatchUpdateResponse:
        """Delete a worksheet by sheet ID."""
        return self._spreadsheets.batch_update(
            spreadsheet_id,
            [{"deleteSheet": {"sheetId": sheet_id}}],
        )

    def duplicate(
        self,
        spreadsheet_id: SpreadsheetId,
        sheet_id: int,
        *,
        new_title: str | None = None,
        insert_index: int | None = None,
    ) -> Worksheet:
        """Duplicate a worksheet; optionally rename and reposition."""
        req: dict[str, Any] = {
            "duplicateSheet": {
                "sourceSheetId": sheet_id,
            }
        }
        if insert_index is not None:
            req["duplicateSheet"]["insertSheetIndex"] = insert_index
        if new_title:
            req["duplicateSheet"]["newSheetName"] = new_title
        resp = self._spreadsheets.batch_update(spreadsheet_id, [req])
        reply = (resp.replies or [{}])[0]
        props = (reply.get("duplicateSheet") or {}).get("properties") or {}
        return Worksheet.from_api({"properties": props})

    def reorder(
        self,
        spreadsheet_id: SpreadsheetId,
        sheet_id: int,
        index: int,
    ) -> BatchUpdateResponse:
        """Move a worksheet to a new zero-based index."""
        if index < 0:
            raise ValidationError("index must be >= 0")
        return self._spreadsheets.batch_update(
            spreadsheet_id,
            [
                {
                    "updateSheetProperties": {
                        "properties": {"sheetId": sheet_id, "index": index},
                        "fields": "index",
                    }
                }
            ],
        )

    def resize(
        self,
        spreadsheet_id: SpreadsheetId,
        sheet_id: int,
        *,
        rows: int | None = None,
        columns: int | None = None,
    ) -> BatchUpdateResponse:
        """Resize the grid (row and/or column count)."""
        if rows is None and columns is None:
            raise ValidationError("Provide rows and/or columns")
        grid: dict[str, Any] = {}
        fields: list[str] = []
        if rows is not None:
            require_positive_int(rows, "rows")
            grid["rowCount"] = rows
            fields.append("gridProperties.rowCount")
        if columns is not None:
            require_positive_int(columns, "columns")
            grid["columnCount"] = columns
            fields.append("gridProperties.columnCount")
        return self._spreadsheets.batch_update(
            spreadsheet_id,
            [
                {
                    "updateSheetProperties": {
                        "properties": {"sheetId": sheet_id, "gridProperties": grid},
                        "fields": ",".join(fields),
                    }
                }
            ],
        )

    def freeze(
        self,
        spreadsheet_id: SpreadsheetId,
        sheet_id: int,
        *,
        rows: int = 0,
        columns: int = 0,
    ) -> BatchUpdateResponse:
        """Freeze the first ``rows`` rows and ``columns`` columns."""
        if rows < 0 or columns < 0:
            raise ValidationError("freeze rows/columns must be >= 0")
        return self._spreadsheets.batch_update(
            spreadsheet_id,
            [
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sheet_id,
                            "gridProperties": {
                                "frozenRowCount": rows,
                                "frozenColumnCount": columns,
                            },
                        },
                        "fields": (
                            "gridProperties.frozenRowCount,gridProperties.frozenColumnCount"
                        ),
                    }
                }
            ],
        )

    def hide(self, spreadsheet_id: SpreadsheetId, sheet_id: int) -> BatchUpdateResponse:
        """Hide a worksheet."""
        return self._set_hidden(spreadsheet_id, sheet_id, True)

    def unhide(self, spreadsheet_id: SpreadsheetId, sheet_id: int) -> BatchUpdateResponse:
        """Unhide a worksheet."""
        return self._set_hidden(spreadsheet_id, sheet_id, False)

    def resolve_sheet_id(
        self,
        spreadsheet_id: SpreadsheetId,
        *,
        sheet_id: int | None = None,
        title: str | None = None,
    ) -> int:
        """Resolve a sheet ID from an ID or title."""
        if sheet_id is not None:
            return sheet_id
        if not title:
            raise ValidationError("Provide sheet_id or title")
        ss = self._spreadsheets.get(spreadsheet_id)
        ws = ss.worksheet_by_title(title)
        if ws is None:
            raise NotFoundError(f"Worksheet not found: {title!r}")
        return ws.sheet_id

    def _set_hidden(
        self,
        spreadsheet_id: SpreadsheetId,
        sheet_id: int,
        hidden: bool,
    ) -> BatchUpdateResponse:
        return self._spreadsheets.batch_update(
            spreadsheet_id,
            [
                {
                    "updateSheetProperties": {
                        "properties": {"sheetId": sheet_id, "hidden": hidden},
                        "fields": "hidden",
                    }
                }
            ],
        )

    def get_spreadsheet(self, spreadsheet_id: SpreadsheetId) -> Spreadsheet:
        """Convenience: fetch full spreadsheet metadata."""
        return self._spreadsheets.get(spreadsheet_id)
