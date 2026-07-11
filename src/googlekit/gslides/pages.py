"""Slide pages manager — add, delete, duplicate, reorder, layouts."""

from __future__ import annotations

from typing import Any

from googlekit.core.exceptions import ValidationError
from googlekit.core.transport import Transport
from googlekit.core.types import PresentationId
from googlekit.core.validation import require_non_empty
from googlekit.gslides.models import BatchUpdateResult, PredefinedLayout, Presentation
from googlekit.gslides.presentations import PresentationsManager


class PagesManager:
    """Manage slides (pages) within a presentation."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport
        self._presentations = PresentationsManager(transport)

    def add(
        self,
        presentation_id: PresentationId,
        *,
        layout: PredefinedLayout | str = PredefinedLayout.BLANK,
        insertion_index: int | None = None,
        object_id: str | None = None,
    ) -> BatchUpdateResult:
        """Add a slide with a predefined layout.

        Args:
            presentation_id: Presentation ID.
            layout: Predefined layout name.
            insertion_index: Zero-based index; append when omitted.
            object_id: Optional stable object ID for the new slide.

        Returns:
            Batch update result (includes createSlide reply with objectId).
        """
        require_non_empty(presentation_id, "presentation_id")
        create: dict[str, Any] = {
            "slideLayoutReference": {"predefinedLayout": str(layout)},
        }
        if insertion_index is not None:
            if insertion_index < 0:
                raise ValidationError("insertion_index must be >= 0")
            create["insertionIndex"] = insertion_index
        if object_id:
            create["objectId"] = object_id
        return self._presentations.batch_update(
            presentation_id,
            [{"createSlide": create}],
        )

    def delete(
        self,
        presentation_id: PresentationId,
        slide_object_id: str,
    ) -> BatchUpdateResult:
        """Delete a slide by object ID."""
        require_non_empty(slide_object_id, "slide_object_id")
        return self._presentations.batch_update(
            presentation_id,
            [{"deleteObject": {"objectId": slide_object_id}}],
        )

    def duplicate(
        self,
        presentation_id: PresentationId,
        slide_object_id: str,
        *,
        object_ids: dict[str, str] | None = None,
    ) -> BatchUpdateResult:
        """Duplicate a slide (and optionally map object IDs).

        Args:
            presentation_id: Presentation ID.
            slide_object_id: Source slide object ID.
            object_ids: Optional map of existing → new object IDs.
        """
        require_non_empty(slide_object_id, "slide_object_id")
        body: dict[str, Any] = {"objectId": slide_object_id}
        if object_ids:
            body["objectIds"] = object_ids
        return self._presentations.batch_update(
            presentation_id,
            [{"duplicateObject": body}],
        )

    def reorder(
        self,
        presentation_id: PresentationId,
        slide_object_ids: list[str],
        insertion_index: int,
    ) -> BatchUpdateResult:
        """Move slides to a new zero-based insertion index.

        Args:
            presentation_id: Presentation ID.
            slide_object_ids: Slide IDs to move (order preserved).
            insertion_index: Destination index among slides.
        """
        if not slide_object_ids:
            raise ValidationError("slide_object_ids must be non-empty")
        if insertion_index < 0:
            raise ValidationError("insertion_index must be >= 0")
        return self._presentations.batch_update(
            presentation_id,
            [
                {
                    "updateSlidesPosition": {
                        "slideObjectIds": list(slide_object_ids),
                        "insertionIndex": insertion_index,
                    }
                }
            ],
        )

    def get_ids(self, presentation_id: PresentationId) -> list[str]:
        """Return ordered slide object IDs."""
        return self._presentations.get(presentation_id).slide_ids()

    def get_page(
        self,
        presentation_id: PresentationId,
        page_object_id: str,
    ) -> dict[str, Any]:
        """Fetch a single page resource (slide, layout, master, or notes).

        Args:
            presentation_id: Presentation ID.
            page_object_id: Page object ID.

        Returns:
            Raw page resource dict from the Slides API.
        """
        pid = require_non_empty(presentation_id, "presentation_id")
        page_id = require_non_empty(page_object_id, "page_object_id")
        service = self._transport.get_service("slides", "v1")
        request = service.presentations().pages().get(presentationId=pid, pageObjectId=page_id)
        return self._transport.execute(request)

    def list_slides(self, presentation_id: PresentationId) -> Presentation:
        """Return the full presentation (convenience for reading slides)."""
        return self._presentations.get(presentation_id)
