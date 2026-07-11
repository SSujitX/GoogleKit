"""Cell formatting helpers via spreadsheets.batchUpdate."""

from __future__ import annotations

from typing import Any

from googlekit.core.exceptions import ValidationError
from googlekit.core.transport import Transport
from googlekit.core.types import SpreadsheetId
from googlekit.core.validation import require_non_empty
from googlekit.gsheets._layout import LayoutFormattingMixin
from googlekit.gsheets._requests import grid_range, repeat_cell_request
from googlekit.gsheets.models import BatchUpdateResponse
from googlekit.gsheets.spreadsheets import SpreadsheetsManager


class FormattingManager(LayoutFormattingMixin):
    """Apply common cell/sheet formatting through batchUpdate requests."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport
        self._spreadsheets = SpreadsheetsManager(transport)

    def text(
        self,
        spreadsheet_id: SpreadsheetId,
        sheet_id: int,
        start_row: int,
        end_row: int,
        start_col: int,
        end_col: int,
        *,
        bold: bool | None = None,
        italic: bool | None = None,
        underline: bool | None = None,
        strikethrough: bool | None = None,
        font_size: int | None = None,
        font_family: str | None = None,
        foreground_color: dict[str, float] | None = None,
    ) -> BatchUpdateResponse:
        """Apply text style to a grid range (0-indexed, end exclusive)."""
        text_format: dict[str, Any] = {}
        fields: list[str] = []
        mapping = {
            "bold": bold,
            "italic": italic,
            "underline": underline,
            "strikethrough": strikethrough,
            "fontSize": font_size,
            "fontFamily": font_family,
            "foregroundColor": foreground_color,
        }
        for key, value in mapping.items():
            if value is not None:
                text_format[key] = value
                fields.append(f"userEnteredFormat.textFormat.{key}")
        if not fields:
            raise ValidationError("Provide at least one text formatting option")
        return self._batch(
            spreadsheet_id,
            [
                repeat_cell_request(
                    sheet_id,
                    start_row,
                    end_row,
                    start_col,
                    end_col,
                    {"userEnteredFormat": {"textFormat": text_format}},
                    ",".join(fields),
                )
            ],
        )

    def number(
        self,
        spreadsheet_id: SpreadsheetId,
        sheet_id: int,
        start_row: int,
        end_row: int,
        start_col: int,
        end_col: int,
        pattern: str,
    ) -> BatchUpdateResponse:
        """Set a number format pattern (e.g. ``0.00%``, ``yyyy-mm-dd``)."""
        require_non_empty(pattern, "pattern")
        return self._batch(
            spreadsheet_id,
            [
                repeat_cell_request(
                    sheet_id,
                    start_row,
                    end_row,
                    start_col,
                    end_col,
                    {"userEnteredFormat": {"numberFormat": {"type": "NUMBER", "pattern": pattern}}},
                    "userEnteredFormat.numberFormat",
                )
            ],
        )

    def background(
        self,
        spreadsheet_id: SpreadsheetId,
        sheet_id: int,
        start_row: int,
        end_row: int,
        start_col: int,
        end_col: int,
        color: dict[str, float],
    ) -> BatchUpdateResponse:
        """Set cell background color (RGB floats 0–1, optional alpha)."""
        if not color:
            raise ValidationError("color must be a non-empty RGB dict")
        return self._batch(
            spreadsheet_id,
            [
                repeat_cell_request(
                    sheet_id,
                    start_row,
                    end_row,
                    start_col,
                    end_col,
                    {"userEnteredFormat": {"backgroundColor": color}},
                    "userEnteredFormat.backgroundColor",
                )
            ],
        )

    def alignment(
        self,
        spreadsheet_id: SpreadsheetId,
        sheet_id: int,
        start_row: int,
        end_row: int,
        start_col: int,
        end_col: int,
        *,
        horizontal: str | None = None,
        vertical: str | None = None,
        wrap_strategy: str | None = None,
    ) -> BatchUpdateResponse:
        """Set horizontal/vertical alignment and wrap strategy."""
        fmt: dict[str, Any] = {}
        fields: list[str] = []
        if horizontal:
            fmt["horizontalAlignment"] = horizontal
            fields.append("userEnteredFormat.horizontalAlignment")
        if vertical:
            fmt["verticalAlignment"] = vertical
            fields.append("userEnteredFormat.verticalAlignment")
        if wrap_strategy:
            fmt["wrapStrategy"] = wrap_strategy
            fields.append("userEnteredFormat.wrapStrategy")
        if not fields:
            raise ValidationError("Provide horizontal, vertical, and/or wrap_strategy")
        return self._batch(
            spreadsheet_id,
            [
                repeat_cell_request(
                    sheet_id,
                    start_row,
                    end_row,
                    start_col,
                    end_col,
                    {"userEnteredFormat": fmt},
                    ",".join(fields),
                )
            ],
        )

    def borders(
        self,
        spreadsheet_id: SpreadsheetId,
        sheet_id: int,
        start_row: int,
        end_row: int,
        start_col: int,
        end_col: int,
        *,
        style: str = "SOLID",
        width: int = 1,
        color: dict[str, float] | None = None,
        top: bool = True,
        bottom: bool = True,
        left: bool = True,
        right: bool = True,
    ) -> BatchUpdateResponse:
        """Apply borders to a range."""
        border: dict[str, Any] = {"style": style, "width": width}
        if color:
            border["color"] = color
        update: dict[str, Any] = {}
        for side, enabled in (
            ("top", top),
            ("bottom", bottom),
            ("left", left),
            ("right", right),
        ):
            if enabled:
                update[side] = border
        if not update:
            raise ValidationError("Enable at least one border side")
        return self._batch(
            spreadsheet_id,
            [
                {
                    "updateBorders": {
                        "range": grid_range(sheet_id, start_row, end_row, start_col, end_col),
                        **update,
                    }
                }
            ],
        )

    def _batch(
        self,
        spreadsheet_id: SpreadsheetId,
        requests: list[dict[str, Any]],
    ) -> BatchUpdateResponse:
        return self._spreadsheets.batch_update(spreadsheet_id, requests)
