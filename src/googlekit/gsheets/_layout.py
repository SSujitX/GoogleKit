"""Layout-oriented Sheets formatting (merge, sizes, conditional rules)."""

from __future__ import annotations

from typing import Any

from googlekit.core.exceptions import ValidationError
from googlekit.core.types import SpreadsheetId
from googlekit.core.validation import require_non_empty
from googlekit.gsheets._requests import dimension_size_request, grid_range
from googlekit.gsheets.models import BatchUpdateResponse


class LayoutFormattingMixin:
    """Mixin providing merge, dimension size, and conditional formatting."""

    def merge(
        self,
        spreadsheet_id: SpreadsheetId,
        sheet_id: int,
        start_row: int,
        end_row: int,
        start_col: int,
        end_col: int,
        *,
        merge_type: str = "MERGE_ALL",
    ) -> BatchUpdateResponse:
        """Merge cells in a range."""
        return self._batch(  # type: ignore[attr-defined]
            spreadsheet_id,
            [
                {
                    "mergeCells": {
                        "range": grid_range(sheet_id, start_row, end_row, start_col, end_col),
                        "mergeType": merge_type,
                    }
                }
            ],
        )

    def unmerge(
        self,
        spreadsheet_id: SpreadsheetId,
        sheet_id: int,
        start_row: int,
        end_row: int,
        start_col: int,
        end_col: int,
    ) -> BatchUpdateResponse:
        """Unmerge cells in a range."""
        return self._batch(  # type: ignore[attr-defined]
            spreadsheet_id,
            [
                {
                    "unmergeCells": {
                        "range": grid_range(sheet_id, start_row, end_row, start_col, end_col)
                    }
                }
            ],
        )

    def column_widths(
        self,
        spreadsheet_id: SpreadsheetId,
        sheet_id: int,
        start_index: int,
        end_index: int,
        pixel_size: int,
    ) -> BatchUpdateResponse:
        """Set column widths (0-indexed, end exclusive) in pixels."""
        return self._batch(  # type: ignore[attr-defined]
            spreadsheet_id,
            [dimension_size_request(sheet_id, "COLUMNS", start_index, end_index, pixel_size)],
        )

    def row_heights(
        self,
        spreadsheet_id: SpreadsheetId,
        sheet_id: int,
        start_index: int,
        end_index: int,
        pixel_size: int,
    ) -> BatchUpdateResponse:
        """Set row heights (0-indexed, end exclusive) in pixels."""
        return self._batch(  # type: ignore[attr-defined]
            spreadsheet_id,
            [dimension_size_request(sheet_id, "ROWS", start_index, end_index, pixel_size)],
        )

    def add_conditional_formatting(
        self,
        spreadsheet_id: SpreadsheetId,
        sheet_id: int,
        start_row: int,
        end_row: int,
        start_col: int,
        end_col: int,
        *,
        formula: str,
        background_color: dict[str, float] | None = None,
        bold: bool | None = None,
        index: int = 0,
    ) -> BatchUpdateResponse:
        """Add a basic boolean conditional format rule (CUSTOM_FORMULA)."""
        require_non_empty(formula, "formula")
        cell_format: dict[str, Any] = {}
        if background_color:
            cell_format["backgroundColor"] = background_color
        if bold is not None:
            cell_format["textFormat"] = {"bold": bold}
        if not cell_format:
            raise ValidationError("Provide background_color and/or bold")
        rule = {
            "ranges": [grid_range(sheet_id, start_row, end_row, start_col, end_col)],
            "booleanRule": {
                "condition": {
                    "type": "CUSTOM_FORMULA",
                    "values": [{"userEnteredValue": formula}],
                },
                "format": cell_format,
            },
        }
        return self._batch(  # type: ignore[attr-defined]
            spreadsheet_id,
            [{"addConditionalFormatRule": {"rule": rule, "index": index}}],
        )
