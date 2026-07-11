"""Document content manager — text, styles, lists, links, named ranges."""

from __future__ import annotations

from typing import Any

from googlekit.core.exceptions import ValidationError
from googlekit.core.transport import Transport
from googlekit.core.types import DocumentId
from googlekit.core.validation import require_non_empty
from googlekit.gdocs.documents import DocumentsManager
from googlekit.gdocs.models import (
    BatchUpdateResult,
    BulletPreset,
    NamedStyleType,
    ParagraphStyle,
    TextRange,
    TextStyle,
)
from googlekit.gdocs.utf16 import offset_utf16, utf16_len


class ContentManager:
    """Insert, delete, replace, and style document text content."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport
        self._documents = DocumentsManager(transport)

    def insert_text(
        self,
        document_id: DocumentId,
        text: str,
        index: int,
        *,
        segment_id: str | None = None,
    ) -> BatchUpdateResult:
        """Insert ``text`` at a UTF-16 ``index``.

        Args:
            document_id: Document ID.
            text: Text to insert (may include newlines to create paragraphs).
            index: UTF-16 insertion index (body content usually starts at 1).
            segment_id: Optional header/footer/footnote segment ID.

        Returns:
            Batch update result.
        """
        require_non_empty(document_id, "document_id")
        if not text:
            raise ValidationError("text must be non-empty")
        if index < 0:
            raise ValidationError("index must be >= 0")
        location: dict[str, Any] = {"index": index}
        if segment_id:
            location["segmentId"] = segment_id
        return self._documents.batch_update(
            document_id,
            [{"insertText": {"location": location, "text": text}}],
        )

    def append_text(self, document_id: DocumentId, text: str) -> BatchUpdateResult:
        """Append ``text`` just before the final newline of the body.

        Args:
            document_id: Document ID.
            text: Text to append.

        Returns:
            Batch update result.
        """
        doc = self._documents.get(document_id)
        if doc.body_end_index is None or doc.body_end_index < 2:
            raise ValidationError("Document body has no valid end index")
        # Insert before the trailing section/body newline.
        return self.insert_text(document_id, text, doc.body_end_index - 1)

    def delete_range(
        self,
        document_id: DocumentId,
        start_index: int,
        end_index: int,
        *,
        segment_id: str | None = None,
    ) -> BatchUpdateResult:
        """Delete the UTF-16 range ``[start_index, end_index)``.

        Args:
            document_id: Document ID.
            start_index: UTF-16 start (inclusive).
            end_index: UTF-16 end (exclusive).
            segment_id: Optional segment ID.

        Returns:
            Batch update result.
        """
        if start_index < 0 or end_index <= start_index:
            raise ValidationError("Invalid delete range")
        rng = TextRange(start_index, end_index, segment_id).to_api()
        return self._documents.batch_update(
            document_id,
            [{"deleteContentRange": {"range": rng}}],
        )

    def replace_all(
        self,
        document_id: DocumentId,
        find_text: str,
        replace_text: str,
        *,
        match_case: bool = True,
    ) -> BatchUpdateResult:
        """Replace all occurrences of ``find_text`` with ``replace_text``.

        Useful for template workflows (e.g. ``{{name}}`` → value).

        Args:
            document_id: Document ID.
            find_text: Text to find.
            replace_text: Replacement text.
            match_case: Case-sensitive match when True.

        Returns:
            Batch update result (reply includes occurrence count when provided).
        """
        require_non_empty(find_text, "find_text")
        return self._documents.batch_update(
            document_id,
            [
                {
                    "replaceAllText": {
                        "containsText": {
                            "text": find_text,
                            "matchCase": match_case,
                        },
                        "replaceText": replace_text,
                    }
                }
            ],
        )

    def replace_placeholders(
        self,
        document_id: DocumentId,
        mapping: dict[str, str],
        *,
        match_case: bool = True,
    ) -> BatchUpdateResult:
        """Replace multiple template placeholders in one batchUpdate.

        Args:
            document_id: Document ID.
            mapping: ``{find_text: replace_text}`` pairs.
            match_case: Case-sensitive match when True.

        Returns:
            Batch update result for all replacements.
        """
        if not mapping:
            raise ValidationError("mapping must be non-empty")
        requests = [
            {
                "replaceAllText": {
                    "containsText": {"text": find, "matchCase": match_case},
                    "replaceText": replace,
                }
            }
            for find, replace in mapping.items()
        ]
        return self._documents.batch_update(document_id, requests)

    def style_text(
        self,
        document_id: DocumentId,
        start_index: int,
        end_index: int,
        style: TextStyle,
        *,
        segment_id: str | None = None,
    ) -> BatchUpdateResult:
        """Apply a :class:`TextStyle` to a UTF-16 range."""
        text_style, fields = style.to_api()
        if not fields:
            raise ValidationError("style has no fields to update")
        rng = TextRange(start_index, end_index, segment_id).to_api()
        return self._documents.batch_update(
            document_id,
            [
                {
                    "updateTextStyle": {
                        "range": rng,
                        "textStyle": text_style,
                        "fields": fields,
                    }
                }
            ],
        )

    def style_paragraph(
        self,
        document_id: DocumentId,
        start_index: int,
        end_index: int,
        style: ParagraphStyle,
        *,
        segment_id: str | None = None,
    ) -> BatchUpdateResult:
        """Apply a :class:`ParagraphStyle` to paragraphs overlapping a range."""
        para_style, fields = style.to_api()
        if not fields:
            raise ValidationError("style has no fields to update")
        rng = TextRange(start_index, end_index, segment_id).to_api()
        return self._documents.batch_update(
            document_id,
            [
                {
                    "updateParagraphStyle": {
                        "range": rng,
                        "paragraphStyle": para_style,
                        "fields": fields,
                    }
                }
            ],
        )

    def set_heading(
        self,
        document_id: DocumentId,
        start_index: int,
        end_index: int,
        heading: NamedStyleType | str,
        *,
        segment_id: str | None = None,
    ) -> BatchUpdateResult:
        """Apply a named heading style to paragraphs in a range."""
        return self.style_paragraph(
            document_id,
            start_index,
            end_index,
            ParagraphStyle(named_style_type=heading),
            segment_id=segment_id,
        )

    def insert_page_break(
        self,
        document_id: DocumentId,
        index: int,
        *,
        segment_id: str | None = None,
    ) -> BatchUpdateResult:
        """Insert a page break at a UTF-16 index."""
        if index < 1:
            raise ValidationError("index must be >= 1")
        location: dict[str, Any] = {"index": index}
        if segment_id:
            location["segmentId"] = segment_id
        return self._documents.batch_update(
            document_id,
            [{"insertPageBreak": {"location": location}}],
        )

    def create_list(
        self,
        document_id: DocumentId,
        start_index: int,
        end_index: int,
        *,
        preset: BulletPreset | str = BulletPreset.BULLET_DISC_CIRCLE_SQUARE,
        segment_id: str | None = None,
    ) -> BatchUpdateResult:
        """Apply bullets / numbering to paragraphs in a range."""
        rng = TextRange(start_index, end_index, segment_id).to_api()
        return self._documents.batch_update(
            document_id,
            [
                {
                    "createParagraphBullets": {
                        "range": rng,
                        "bulletPreset": str(preset),
                    }
                }
            ],
        )

    def delete_list(
        self,
        document_id: DocumentId,
        start_index: int,
        end_index: int,
        *,
        segment_id: str | None = None,
    ) -> BatchUpdateResult:
        """Remove bullets / numbering from paragraphs in a range."""
        rng = TextRange(start_index, end_index, segment_id).to_api()
        return self._documents.batch_update(
            document_id,
            [{"deleteParagraphBullets": {"range": rng}}],
        )

    def insert_link(
        self,
        document_id: DocumentId,
        start_index: int,
        end_index: int,
        url: str,
        *,
        segment_id: str | None = None,
    ) -> BatchUpdateResult:
        """Turn a text range into a hyperlink."""
        require_non_empty(url, "url")
        return self.style_text(
            document_id,
            start_index,
            end_index,
            TextStyle(link_url=url),
            segment_id=segment_id,
        )

    def create_named_range(
        self,
        document_id: DocumentId,
        name: str,
        start_index: int,
        end_index: int,
        *,
        segment_id: str | None = None,
    ) -> BatchUpdateResult:
        """Create a named range over a UTF-16 span."""
        require_non_empty(name, "name")
        rng = TextRange(start_index, end_index, segment_id).to_api()
        return self._documents.batch_update(
            document_id,
            [{"createNamedRange": {"name": name, "range": rng}}],
        )

    def delete_named_range(
        self,
        document_id: DocumentId,
        *,
        name: str | None = None,
        named_range_id: str | None = None,
    ) -> BatchUpdateResult:
        """Delete named range(s) by name or ID."""
        if not name and not named_range_id:
            raise ValidationError("Provide name or named_range_id")
        body: dict[str, Any] = {}
        if name:
            body["name"] = name
        if named_range_id:
            body["namedRangeId"] = named_range_id
        return self._documents.batch_update(
            document_id,
            [{"deleteNamedRange": body}],
        )

    def insert_styled_text(
        self,
        document_id: DocumentId,
        text: str,
        index: int,
        style: TextStyle,
        *,
        segment_id: str | None = None,
    ) -> BatchUpdateResult:
        """Insert text and immediately apply styling to the inserted span."""
        end = offset_utf16(index, text)
        location: dict[str, Any] = {"index": index}
        if segment_id:
            location["segmentId"] = segment_id
        text_style, fields = style.to_api()
        if not fields:
            raise ValidationError("style has no fields to update")
        requests: list[dict[str, Any]] = [
            {"insertText": {"location": location, "text": text}},
            {
                "updateTextStyle": {
                    "range": TextRange(index, end, segment_id).to_api(),
                    "textStyle": text_style,
                    "fields": fields,
                }
            },
        ]
        return self._documents.batch_update(document_id, requests)

    @staticmethod
    def text_utf16_length(text: str) -> int:
        """Return UTF-16 length of ``text`` (Docs index units)."""
        return utf16_len(text)
