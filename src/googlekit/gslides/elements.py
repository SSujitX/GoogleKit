"""Page elements manager — shapes, move, resize, group/ungroup."""

from __future__ import annotations

from typing import Any

from googlekit.core.exceptions import NotFoundError, ValidationError
from googlekit.core.transport import Transport
from googlekit.core.types import PresentationId
from googlekit.core.validation import require_non_empty
from googlekit.gslides.models import (
    AffineTransform,
    BatchUpdateResult,
    PageElement,
    Presentation,
    ShapeType,
    Size,
    pt_to_emu,
)
from googlekit.gslides.presentations import PresentationsManager


class ElementsManager:
    """Create and transform page elements on slides."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport
        self._presentations = PresentationsManager(transport)

    def _find_element(self, presentation_id: PresentationId, object_id: str) -> PageElement:
        presentation: Presentation = self._presentations.get(presentation_id)
        for slide in presentation.slides:
            for element in slide.elements:
                if element.object_id == object_id:
                    return element
        raise NotFoundError(f"Page element {object_id!r} not found in presentation")

    def create_shape(
        self,
        presentation_id: PresentationId,
        page_object_id: str,
        shape_type: ShapeType | str = ShapeType.TEXT_BOX,
        *,
        size: Size | None = None,
        transform: AffineTransform | None = None,
        object_id: str | None = None,
        width_pt: float = 300.0,
        height_pt: float = 100.0,
        x_pt: float = 50.0,
        y_pt: float = 50.0,
    ) -> BatchUpdateResult:
        """Create a shape on a slide.

        Args:
            presentation_id: Presentation ID.
            page_object_id: Target slide object ID.
            shape_type: Shape type (e.g. TEXT_BOX, RECTANGLE).
            size: Optional explicit size in EMUs.
            transform: Optional explicit transform.
            object_id: Optional stable object ID.
            width_pt: Default width when ``size`` is omitted.
            height_pt: Default height when ``size`` is omitted.
            x_pt: Default X translation in points when ``transform`` omitted.
            y_pt: Default Y translation in points when ``transform`` omitted.
        """
        require_non_empty(page_object_id, "page_object_id")
        sz = size or Size.from_pt(width_pt, height_pt)
        tf = transform or AffineTransform.translate_pt(x_pt, y_pt)
        create: dict[str, Any] = {
            "shapeType": str(shape_type),
            "elementProperties": {
                "pageObjectId": page_object_id,
                "size": sz.to_api(),
                "transform": tf.to_api(),
            },
        }
        if object_id:
            create["objectId"] = object_id
        return self._presentations.batch_update(
            presentation_id,
            [{"createShape": create}],
        )

    def delete(
        self,
        presentation_id: PresentationId,
        object_id: str,
    ) -> BatchUpdateResult:
        """Delete a page element by object ID."""
        require_non_empty(object_id, "object_id")
        return self._presentations.batch_update(
            presentation_id,
            [{"deleteObject": {"objectId": object_id}}],
        )

    def move(
        self,
        presentation_id: PresentationId,
        object_id: str,
        *,
        x_pt: float,
        y_pt: float,
        apply_mode: str = "ABSOLUTE",
    ) -> BatchUpdateResult:
        """Move an element by setting its translation (points → EMU).

        ABSOLUTE updates replace the full transform; current scale/shear are
        preserved so sized elements are not reset to scale 1.
        """
        require_non_empty(object_id, "object_id")
        current = self._find_element(presentation_id, object_id).transform or AffineTransform()
        tf = AffineTransform(
            scale_x=current.scale_x,
            scale_y=current.scale_y,
            shear_x=current.shear_x,
            shear_y=current.shear_y,
            translate_x_emu=float(pt_to_emu(x_pt)),
            translate_y_emu=float(pt_to_emu(y_pt)),
            unit=current.unit,
        )
        return self._presentations.batch_update(
            presentation_id,
            [
                {
                    "updatePageElementTransform": {
                        "objectId": object_id,
                        "transform": tf.to_api(),
                        "applyMode": apply_mode,
                    }
                }
            ],
        )

    def resize(
        self,
        presentation_id: PresentationId,
        object_id: str,
        *,
        width_pt: float,
        height_pt: float,
        x_pt: float | None = None,
        y_pt: float | None = None,
        apply_mode: str = "ABSOLUTE",
    ) -> BatchUpdateResult:
        """Resize an element relative to its current ``size`` property.

        Create paths set full EMU size with ``scaleX/Y = 1``. ABSOLUTE resize
        therefore sets ``scale = target_emu / current_size_emu`` (not raw EMU
        magnitudes, which would inflate by ~12700×).
        """
        require_non_empty(object_id, "object_id")
        if width_pt <= 0 or height_pt <= 0:
            raise ValidationError("width_pt and height_pt must be positive")
        element = self._find_element(presentation_id, object_id)
        if element.size is None or element.size.width_emu <= 0 or element.size.height_emu <= 0:
            raise ValidationError(
                f"Element {object_id!r} has no usable size; cannot compute resize scale"
            )
        current = element.transform or AffineTransform()
        tx = float(pt_to_emu(x_pt)) if x_pt is not None else current.translate_x_emu
        ty = float(pt_to_emu(y_pt)) if y_pt is not None else current.translate_y_emu
        tf = AffineTransform(
            scale_x=float(pt_to_emu(width_pt)) / element.size.width_emu,
            scale_y=float(pt_to_emu(height_pt)) / element.size.height_emu,
            shear_x=current.shear_x,
            shear_y=current.shear_y,
            translate_x_emu=tx,
            translate_y_emu=ty,
            unit=current.unit,
        )
        return self._presentations.batch_update(
            presentation_id,
            [
                {
                    "updatePageElementTransform": {
                        "objectId": object_id,
                        "transform": tf.to_api(),
                        "applyMode": apply_mode,
                    }
                }
            ],
        )

    def set_transform(
        self,
        presentation_id: PresentationId,
        object_id: str,
        transform: AffineTransform,
        *,
        apply_mode: str = "ABSOLUTE",
    ) -> BatchUpdateResult:
        """Set an element's affine transform explicitly."""
        require_non_empty(object_id, "object_id")
        return self._presentations.batch_update(
            presentation_id,
            [
                {
                    "updatePageElementTransform": {
                        "objectId": object_id,
                        "transform": transform.to_api(),
                        "applyMode": apply_mode,
                    }
                }
            ],
        )

    def group(
        self,
        presentation_id: PresentationId,
        object_ids: list[str],
        *,
        group_object_id: str | None = None,
    ) -> BatchUpdateResult:
        """Group page elements (Slides ``groupObjects``)."""
        if len(object_ids) < 2:
            raise ValidationError("group requires at least two object_ids")
        body: dict[str, Any] = {"childrenObjectIds": list(object_ids)}
        if group_object_id:
            body["groupObjectId"] = group_object_id
        return self._presentations.batch_update(
            presentation_id,
            [{"groupObjects": body}],
        )

    def ungroup(
        self,
        presentation_id: PresentationId,
        object_ids: list[str],
    ) -> BatchUpdateResult:
        """Ungroup one or more group objects."""
        if not object_ids:
            raise ValidationError("object_ids must be non-empty")
        return self._presentations.batch_update(
            presentation_id,
            [{"ungroupObjects": {"objectIds": list(object_ids)}}],
        )
