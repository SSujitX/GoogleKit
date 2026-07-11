"""Slide tables manager."""

from __future__ import annotations

from typing import Any

from googlekit.core.exceptions import ValidationError
from googlekit.core.transport import Transport
from googlekit.core.types import PresentationId
from googlekit.core.validation import require_non_empty, require_positive_int
from googlekit.gslides.models import AffineTransform, BatchUpdateResult, Size, TextStyle
from googlekit.gslides.presentations import PresentationsManager


class TablesManager:
    """Create and edit tables on slides."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport
        self._presentations = PresentationsManager(transport)

    def create(
        self,
        presentation_id: PresentationId,
        page_object_id: str,
        rows: int,
        columns: int,
        *,
        size: Size | None = None,
        transform: AffineTransform | None = None,
        object_id: str | None = None,
        width_pt: float = 400.0,
        height_pt: float = 200.0,
        x_pt: float = 50.0,
        y_pt: float = 50.0,
    ) -> BatchUpdateResult:
        """Create a table on a slide."""
        require_non_empty(page_object_id, "page_object_id")
        require_positive_int(rows, "rows")
        require_positive_int(columns, "columns")
        sz = size or Size.from_pt(width_pt, height_pt)
        tf = transform or AffineTransform.translate_pt(x_pt, y_pt)
        element: dict[str, Any] = {
            "pageObjectId": page_object_id,
            "size": sz.to_api(),
            "transform": tf.to_api(),
        }
        create: dict[str, Any] = {
            "rows": rows,
            "columns": columns,
            "elementProperties": element,
        }
        if object_id:
            create["objectId"] = object_id
        return self._presentations.batch_update(
            presentation_id,
            [{"createTable": create}],
        )

    def write_cell(
        self,
        presentation_id: PresentationId,
        table_object_id: str,
        row_index: int,
        column_index: int,
        text: str,
        *,
        style: TextStyle | None = None,
    ) -> BatchUpdateResult:
        """Write text into a table cell (replaces existing cell text).

        Cell text object IDs follow the Slides convention
        ``{tableId}_R{row}_C{column}`` when using auto-generated IDs. Prefer
        passing the cell's text object ID via ``table_object_id`` when known;
        otherwise this method uses the conventional ID pattern.
        """
        require_non_empty(table_object_id, "table_object_id")
        if row_index < 0 or column_index < 0:
            raise ValidationError("row_index and column_index must be >= 0")
        if not text:
            raise ValidationError("text must be non-empty")
        cell_id = f"{table_object_id}_R{row_index}_C{column_index}"
        requests: list[dict[str, Any]] = [
            {
                "deleteText": {
                    "objectId": cell_id,
                    "textRange": {"type": "ALL"},
                }
            },
            {
                "insertText": {
                    "objectId": cell_id,
                    "text": text,
                    "insertionIndex": 0,
                }
            },
        ]
        if style is not None:
            text_style, fields = style.to_api()
            if fields:
                requests.append(
                    {
                        "updateTextStyle": {
                            "objectId": cell_id,
                            "style": text_style,
                            "textRange": {"type": "ALL"},
                            "fields": fields,
                        }
                    }
                )
        return self._presentations.batch_update(presentation_id, requests)

    def insert_rows(
        self,
        presentation_id: PresentationId,
        table_object_id: str,
        *,
        number: int = 1,
        insert_below: bool = True,
        row_index: int = 0,
    ) -> BatchUpdateResult:
        """Insert rows into a table."""
        require_non_empty(table_object_id, "table_object_id")
        require_positive_int(number, "number")
        return self._presentations.batch_update(
            presentation_id,
            [
                {
                    "insertTableRows": {
                        "tableObjectId": table_object_id,
                        "insertBelow": insert_below,
                        "number": number,
                        "cellLocation": {"rowIndex": row_index, "columnIndex": 0},
                    }
                }
            ],
        )

    def insert_columns(
        self,
        presentation_id: PresentationId,
        table_object_id: str,
        *,
        number: int = 1,
        insert_right: bool = True,
        column_index: int = 0,
    ) -> BatchUpdateResult:
        """Insert columns into a table."""
        require_non_empty(table_object_id, "table_object_id")
        require_positive_int(number, "number")
        return self._presentations.batch_update(
            presentation_id,
            [
                {
                    "insertTableColumns": {
                        "tableObjectId": table_object_id,
                        "insertRight": insert_right,
                        "number": number,
                        "cellLocation": {"rowIndex": 0, "columnIndex": column_index},
                    }
                }
            ],
        )

    def delete_row(
        self,
        presentation_id: PresentationId,
        table_object_id: str,
        row_index: int,
    ) -> BatchUpdateResult:
        """Delete a table row."""
        require_non_empty(table_object_id, "table_object_id")
        if row_index < 0:
            raise ValidationError("row_index must be >= 0")
        return self._presentations.batch_update(
            presentation_id,
            [
                {
                    "deleteTableRow": {
                        "tableObjectId": table_object_id,
                        "cellLocation": {"rowIndex": row_index, "columnIndex": 0},
                    }
                }
            ],
        )

    def delete_column(
        self,
        presentation_id: PresentationId,
        table_object_id: str,
        column_index: int,
    ) -> BatchUpdateResult:
        """Delete a table column."""
        require_non_empty(table_object_id, "table_object_id")
        if column_index < 0:
            raise ValidationError("column_index must be >= 0")
        return self._presentations.batch_update(
            presentation_id,
            [
                {
                    "deleteTableColumn": {
                        "tableObjectId": table_object_id,
                        "cellLocation": {"rowIndex": 0, "columnIndex": column_index},
                    }
                }
            ],
        )

    def format_cells(
        self,
        presentation_id: PresentationId,
        table_object_id: str,
        *,
        row_index: int,
        column_index: int,
        row_span: int = 1,
        column_span: int = 1,
        background_color: dict[str, Any] | None = None,
    ) -> BatchUpdateResult:
        """Apply basic cell formatting (background color)."""
        require_non_empty(table_object_id, "table_object_id")
        if background_color is None:
            raise ValidationError("background_color is required")
        return self._presentations.batch_update(
            presentation_id,
            [
                {
                    "updateTableCellProperties": {
                        "objectId": table_object_id,
                        "tableRange": {
                            "location": {
                                "rowIndex": row_index,
                                "columnIndex": column_index,
                            },
                            "rowSpan": row_span,
                            "columnSpan": column_span,
                        },
                        "tableCellProperties": {
                            "tableCellBackgroundFill": {"solidFill": {"color": background_color}}
                        },
                        "fields": "tableCellBackgroundFill.solidFill.color",
                    }
                }
            ],
        )
