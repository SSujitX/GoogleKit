"""Low-level Sheets batchUpdate request builders."""

from __future__ import annotations

from typing import Any

from googlekit.core.exceptions import ValidationError


def grid_range(
    sheet_id: int,
    start_row: int,
    end_row: int,
    start_col: int,
    end_col: int,
) -> dict[str, int]:
    """Build a GridRange (0-indexed, end exclusive)."""
    if start_row < 0 or start_col < 0 or end_row <= start_row or end_col <= start_col:
        raise ValidationError("Invalid grid range (0-indexed, end exclusive)")
    return {
        "sheetId": sheet_id,
        "startRowIndex": start_row,
        "endRowIndex": end_row,
        "startColumnIndex": start_col,
        "endColumnIndex": end_col,
    }


def repeat_cell_request(
    sheet_id: int,
    start_row: int,
    end_row: int,
    start_col: int,
    end_col: int,
    cell: dict[str, Any],
    fields: str,
) -> dict[str, Any]:
    return {
        "repeatCell": {
            "range": grid_range(sheet_id, start_row, end_row, start_col, end_col),
            "cell": cell,
            "fields": fields,
        }
    }


def dimension_size_request(
    sheet_id: int,
    dimension: str,
    start_index: int,
    end_index: int,
    pixel_size: int,
) -> dict[str, Any]:
    if start_index < 0 or end_index <= start_index:
        raise ValidationError("Invalid dimension index range")
    if pixel_size < 0:
        raise ValidationError("pixel_size must be >= 0")
    return {
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": dimension,
                "startIndex": start_index,
                "endIndex": end_index,
            },
            "properties": {"pixelSize": pixel_size},
            "fields": "pixelSize",
        }
    }
