"""Slide text manager — insert, replace, delete, style, placeholders."""

from __future__ import annotations

from typing import Any

from googlekit.core.exceptions import ValidationError
from googlekit.core.transport import Transport
from googlekit.core.types import PresentationId
from googlekit.core.validation import require_non_empty
from googlekit.gslides.models import BatchUpdateResult, ParagraphStyle, TextStyle
from googlekit.gslides.presentations import PresentationsManager


class TextManager:
    """Manipulate text inside shapes and tables on slides."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport
        self._presentations = PresentationsManager(transport)

    def insert(
        self,
        presentation_id: PresentationId,
        object_id: str,
        text: str,
        *,
        insertion_index: int = 0,
    ) -> BatchUpdateResult:
        """Insert text into a shape or table cell text.

        Args:
            presentation_id: Presentation ID.
            object_id: Shape / cell object ID containing text.
            text: Text to insert.
            insertion_index: Character index within the text element.
        """
        require_non_empty(object_id, "object_id")
        if not text:
            raise ValidationError("text must be non-empty")
        if insertion_index < 0:
            raise ValidationError("insertion_index must be >= 0")
        return self._presentations.batch_update(
            presentation_id,
            [
                {
                    "insertText": {
                        "objectId": object_id,
                        "text": text,
                        "insertionIndex": insertion_index,
                    }
                }
            ],
        )

    def delete(
        self,
        presentation_id: PresentationId,
        object_id: str,
        *,
        start_index: int = 0,
        end_index: int | None = None,
    ) -> BatchUpdateResult:
        """Delete text from a shape.

        When ``end_index`` is omitted, deletes all text (``ALL`` range type).
        """
        require_non_empty(object_id, "object_id")
        if end_index is None:
            text_range: dict[str, Any] = {"type": "ALL"}
        else:
            if end_index <= start_index:
                raise ValidationError("end_index must be > start_index")
            text_range = {
                "type": "FIXED_RANGE",
                "startIndex": start_index,
                "endIndex": end_index,
            }
        return self._presentations.batch_update(
            presentation_id,
            [{"deleteText": {"objectId": object_id, "textRange": text_range}}],
        )

    def replace_all(
        self,
        presentation_id: PresentationId,
        find_text: str,
        replace_text: str,
        *,
        match_case: bool = True,
        page_object_ids: list[str] | None = None,
    ) -> BatchUpdateResult:
        """Replace all occurrences of text across the presentation (or pages)."""
        require_non_empty(find_text, "find_text")
        body: dict[str, Any] = {
            "containsText": {"text": find_text, "matchCase": match_case},
            "replaceText": replace_text,
        }
        if page_object_ids:
            body["pageObjectIds"] = list(page_object_ids)
        return self._presentations.batch_update(
            presentation_id,
            [{"replaceAllText": body}],
        )

    def replace_placeholders(
        self,
        presentation_id: PresentationId,
        mapping: dict[str, str],
        *,
        match_case: bool = True,
        page_object_ids: list[str] | None = None,
    ) -> BatchUpdateResult:
        """Replace multiple template placeholders in one batchUpdate.

        Ideal for deck templates such as ``{{title}}`` / ``{{name}}``.
        """
        if not mapping:
            raise ValidationError("mapping must be non-empty")
        requests: list[dict[str, Any]] = []
        for find, replace in mapping.items():
            body: dict[str, Any] = {
                "containsText": {"text": find, "matchCase": match_case},
                "replaceText": replace,
            }
            if page_object_ids:
                body["pageObjectIds"] = list(page_object_ids)
            requests.append({"replaceAllText": body})
        return self._presentations.batch_update(presentation_id, requests)

    def style(
        self,
        presentation_id: PresentationId,
        object_id: str,
        style: TextStyle,
        *,
        start_index: int = 0,
        end_index: int | None = None,
    ) -> BatchUpdateResult:
        """Apply text styling to a range (or all text)."""
        require_non_empty(object_id, "object_id")
        text_style, fields = style.to_api()
        if not fields:
            raise ValidationError("style has no fields to update")
        if end_index is None:
            text_range: dict[str, Any] = {"type": "ALL"}
        else:
            text_range = {
                "type": "FIXED_RANGE",
                "startIndex": start_index,
                "endIndex": end_index,
            }
        return self._presentations.batch_update(
            presentation_id,
            [
                {
                    "updateTextStyle": {
                        "objectId": object_id,
                        "style": text_style,
                        "textRange": text_range,
                        "fields": fields,
                    }
                }
            ],
        )

    def style_paragraph(
        self,
        presentation_id: PresentationId,
        object_id: str,
        style: ParagraphStyle,
        *,
        start_index: int = 0,
        end_index: int | None = None,
    ) -> BatchUpdateResult:
        """Apply paragraph styling to a range (or all paragraphs)."""
        require_non_empty(object_id, "object_id")
        para_style, fields = style.to_api()
        if not fields:
            raise ValidationError("style has no fields to update")
        if end_index is None:
            text_range: dict[str, Any] = {"type": "ALL"}
        else:
            text_range = {
                "type": "FIXED_RANGE",
                "startIndex": start_index,
                "endIndex": end_index,
            }
        return self._presentations.batch_update(
            presentation_id,
            [
                {
                    "updateParagraphStyle": {
                        "objectId": object_id,
                        "style": para_style,
                        "textRange": text_range,
                        "fields": fields,
                    }
                }
            ],
        )
