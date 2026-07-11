"""Document inline images manager."""

from __future__ import annotations

from typing import Any

from googlekit.core.exceptions import ValidationError
from googlekit.core.transport import Transport
from googlekit.core.types import DocumentId
from googlekit.core.validation import require_non_empty
from googlekit.gdocs.documents import DocumentsManager
from googlekit.gdocs.models import BatchUpdateResult


class ImagesManager:
    """Insert, resize, and replace inline images in a Google Doc."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport
        self._documents = DocumentsManager(transport)

    def insert_from_url(
        self,
        document_id: DocumentId,
        url: str,
        index: int,
        *,
        width_pt: float | None = None,
        height_pt: float | None = None,
        segment_id: str | None = None,
    ) -> BatchUpdateResult:
        """Insert an inline image from a publicly accessible URL.

        Args:
            document_id: Document ID.
            url: Public HTTPS URL of the image.
            index: UTF-16 insertion index.
            width_pt: Optional width in points.
            height_pt: Optional height in points.
            segment_id: Optional segment ID.

        Returns:
            Batch update result (reply may include the object ID).
        """
        require_non_empty(document_id, "document_id")
        require_non_empty(url, "url")
        if index < 1:
            raise ValidationError("index must be >= 1")
        location: dict[str, Any] = {"index": index}
        if segment_id:
            location["segmentId"] = segment_id
        body: dict[str, Any] = {"uri": url, "location": location}
        object_size: dict[str, Any] = {}
        if width_pt is not None:
            if width_pt <= 0:
                raise ValidationError("width_pt must be positive")
            object_size["width"] = {"magnitude": width_pt, "unit": "PT"}
        if height_pt is not None:
            if height_pt <= 0:
                raise ValidationError("height_pt must be positive")
            object_size["height"] = {"magnitude": height_pt, "unit": "PT"}
        if object_size:
            body["objectSize"] = object_size
        return self._documents.batch_update(
            document_id,
            [{"insertInlineImage": body}],
        )

    def resize(
        self,
        document_id: DocumentId,
        start_index: int,
        url: str,
        *,
        width_pt: float,
        height_pt: float,
        end_index: int | None = None,
    ) -> BatchUpdateResult:
        """Resize an inline image by deleting its range and re-inserting.

        The Docs API has no dedicated resize-by-index request. This helper
        deletes ``[start_index, end_index)`` and inserts the image from ``url``
        with the given dimensions.

        Args:
            document_id: Document ID.
            start_index: UTF-16 start of the existing image element.
            url: Public image URL (same or new).
            width_pt: New width in points.
            height_pt: New height in points.
            end_index: UTF-16 end; defaults to ``start_index + 1``.
        """
        require_non_empty(url, "url")
        if width_pt <= 0 or height_pt <= 0:
            raise ValidationError("width_pt and height_pt must be positive")
        end = end_index if end_index is not None else start_index + 1
        if start_index < 1 or end <= start_index:
            raise ValidationError("Invalid image range")
        return self._documents.batch_update(
            document_id,
            [
                {"deleteContentRange": {"range": {"startIndex": start_index, "endIndex": end}}},
                {
                    "insertInlineImage": {
                        "uri": url,
                        "location": {"index": start_index},
                        "objectSize": {
                            "width": {"magnitude": width_pt, "unit": "PT"},
                            "height": {"magnitude": height_pt, "unit": "PT"},
                        },
                    }
                },
            ],
        )

    def replace(
        self,
        document_id: DocumentId,
        object_id: str,
        url: str,
        *,
        image_replace_method: str = "CENTER_CROP",
    ) -> BatchUpdateResult:
        """Replace an inline image by object ID.

        Args:
            document_id: Document ID.
            object_id: Existing inline image object ID.
            url: Public URL of the replacement image.
            image_replace_method: Docs ``ImageReplaceMethod`` value.
        """
        require_non_empty(object_id, "object_id")
        require_non_empty(url, "url")
        return self._documents.batch_update(
            document_id,
            [
                {
                    "replaceImage": {
                        "imageObjectId": object_id,
                        "uri": url,
                        "imageReplaceMethod": image_replace_method,
                    }
                }
            ],
        )
