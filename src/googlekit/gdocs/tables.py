"""Document tables manager."""

from __future__ import annotations

from typing import Any

from googlekit.core.exceptions import ValidationError
from googlekit.core.transport import Transport
from googlekit.core.types import DocumentId
from googlekit.core.validation import require_non_empty, require_positive_int
from googlekit.gdocs.documents import DocumentsManager
from googlekit.gdocs.models import BatchUpdateResult, TextStyle


class TablesManager:
    """Insert and mutate tables inside a Google Doc."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport
        self._documents = DocumentsManager(transport)

    def insert_table(
        self,
        document_id: DocumentId,
        rows: int,
        columns: int,
        index: int,
        *,
        segment_id: str | None = None,
    ) -> BatchUpdateResult:
        """Insert an empty table at a UTF-16 index.

        Args:
            document_id: Document ID.
            rows: Number of rows (>= 1).
            columns: Number of columns (>= 1).
            index: UTF-16 insertion index.
            segment_id: Optional segment ID.

        Returns:
            Batch update result.
        """
        require_non_empty(document_id, "document_id")
        require_positive_int(rows, "rows")
        require_positive_int(columns, "columns")
        if index < 1:
            raise ValidationError("index must be >= 1")
        location: dict[str, Any] = {"index": index}
        if segment_id:
            location["segmentId"] = segment_id
        return self._documents.batch_update(
            document_id,
            [
                {
                    "insertTable": {
                        "rows": rows,
                        "columns": columns,
                        "location": location,
                    }
                }
            ],
        )

    def insert_rows(
        self,
        document_id: DocumentId,
        table_start_index: int,
        row_index: int,
        *,
        insert_below: bool = True,
        number: int = 1,
    ) -> BatchUpdateResult:
        """Insert one or more rows into a table.

        Args:
            document_id: Document ID.
            table_start_index: UTF-16 start index of the table.
            row_index: Existing row index to insert relative to (0-based).
            insert_below: Insert below ``row_index`` when True, else above.
            number: Number of rows to insert.
        """
        require_positive_int(number, "number")
        if table_start_index < 1:
            raise ValidationError("table_start_index must be >= 1")
        if row_index < 0:
            raise ValidationError("row_index must be >= 0")
        return self._documents.batch_update(
            document_id,
            [
                {
                    "insertTableRow": {
                        "tableCellLocation": {
                            "tableStartLocation": {"index": table_start_index},
                            "rowIndex": row_index,
                            "columnIndex": 0,
                        },
                        "insertBelow": insert_below,
                    }
                }
                for _ in range(number)
            ],
        )

    def delete_row(
        self,
        document_id: DocumentId,
        table_start_index: int,
        row_index: int,
    ) -> BatchUpdateResult:
        """Delete a table row."""
        if row_index < 0:
            raise ValidationError("row_index must be >= 0")
        return self._documents.batch_update(
            document_id,
            [
                {
                    "deleteTableRow": {
                        "tableCellLocation": {
                            "tableStartLocation": {"index": table_start_index},
                            "rowIndex": row_index,
                            "columnIndex": 0,
                        }
                    }
                }
            ],
        )

    def insert_columns(
        self,
        document_id: DocumentId,
        table_start_index: int,
        column_index: int,
        *,
        insert_right: bool = True,
        number: int = 1,
    ) -> BatchUpdateResult:
        """Insert one or more columns into a table."""
        require_positive_int(number, "number")
        if column_index < 0:
            raise ValidationError("column_index must be >= 0")
        return self._documents.batch_update(
            document_id,
            [
                {
                    "insertTableColumn": {
                        "tableCellLocation": {
                            "tableStartLocation": {"index": table_start_index},
                            "rowIndex": 0,
                            "columnIndex": column_index,
                        },
                        "insertRight": insert_right,
                    }
                }
                for _ in range(number)
            ],
        )

    def delete_column(
        self,
        document_id: DocumentId,
        table_start_index: int,
        column_index: int,
    ) -> BatchUpdateResult:
        """Delete a table column."""
        if column_index < 0:
            raise ValidationError("column_index must be >= 0")
        return self._documents.batch_update(
            document_id,
            [
                {
                    "deleteTableColumn": {
                        "tableCellLocation": {
                            "tableStartLocation": {"index": table_start_index},
                            "rowIndex": 0,
                            "columnIndex": column_index,
                        }
                    }
                }
            ],
        )

    def write_cell(
        self,
        document_id: DocumentId,
        cell_start_index: int,
        text: str,
        *,
        style: TextStyle | None = None,
    ) -> BatchUpdateResult:
        """Write text into a table cell at its content start index.

        The ``cell_start_index`` must be the UTF-16 index of the first content
        character inside the cell (typically cell start + 1). Existing cell
        content (except the trailing newline) should be deleted by the caller
        when replacing.

        Args:
            document_id: Document ID.
            cell_start_index: UTF-16 index inside the cell for insertion.
            text: Text to insert.
            style: Optional text style applied to the inserted text.
        """
        if not text:
            raise ValidationError("text must be non-empty")
        if cell_start_index < 1:
            raise ValidationError("cell_start_index must be >= 1")
        requests: list[dict[str, Any]] = [
            {
                "insertText": {
                    "location": {"index": cell_start_index},
                    "text": text,
                }
            }
        ]
        if style is not None:
            text_style, fields = style.to_api()
            if fields:
                from googlekit.gdocs.utf16 import offset_utf16

                end = offset_utf16(cell_start_index, text)
                requests.append(
                    {
                        "updateTextStyle": {
                            "range": {
                                "startIndex": cell_start_index,
                                "endIndex": end,
                            },
                            "textStyle": text_style,
                            "fields": fields,
                        }
                    }
                )
        return self._documents.batch_update(document_id, requests)

    def format_cell(
        self,
        document_id: DocumentId,
        table_start_index: int,
        *,
        row_index: int = 0,
        column_index: int = 0,
        row_span: int = 1,
        column_span: int = 1,
        background_color: dict[str, Any] | None = None,
        border_color: dict[str, Any] | None = None,
        border_width_pt: float | None = None,
    ) -> BatchUpdateResult:
        """Apply basic table cell style via ``updateTableCellStyle``.

        ``table_start_index`` is the Docs index of the table start (not a content
        range). Colors should be Docs ``OptionalColor`` objects
        (e.g. ``{"color": {"rgbColor": {...}}}``).
        """
        if row_index < 0 or column_index < 0:
            raise ValidationError("row_index and column_index must be >= 0")
        if row_span < 1 or column_span < 1:
            raise ValidationError("row_span and column_span must be >= 1")
        style: dict[str, Any] = {}
        fields: list[str] = []
        if background_color is not None:
            style["backgroundColor"] = background_color
            fields.append("backgroundColor")
        if border_color is not None or border_width_pt is not None:
            border: dict[str, Any] = {"dashStyle": "SOLID"}
            if border_color is not None:
                border["color"] = border_color
            if border_width_pt is not None:
                border["width"] = {"magnitude": border_width_pt, "unit": "PT"}
            # Official TableCellStyle uses borderTop/Bottom/Left/Right.
            for edge in ("borderTop", "borderBottom", "borderLeft", "borderRight"):
                style[edge] = dict(border)
                fields.append(edge)
        if not fields:
            raise ValidationError("Provide at least one formatting option")
        return self._documents.batch_update(
            document_id,
            [
                {
                    "updateTableCellStyle": {
                        "tableRange": {
                            "tableCellLocation": {
                                "tableStartLocation": {"index": table_start_index},
                                "rowIndex": row_index,
                                "columnIndex": column_index,
                            },
                            "rowSpan": row_span,
                            "columnSpan": column_span,
                        },
                        "tableCellStyle": style,
                        "fields": ",".join(fields),
                    }
                }
            ],
        )
