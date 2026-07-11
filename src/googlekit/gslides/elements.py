"""Page elements manager — shapes, move, resize, group/ungroup."""

from __future__ import annotations

from typing import Any

from googlekit.core.exceptions import ValidationError
from googlekit.core.transport import Transport
from googlekit.core.types import PresentationId
from googlekit.core.validation import require_non_empty
from googlekit.gslides.models import (
    AffineTransform,
    BatchUpdateResult,
    ShapeType,
    Size,
)
from googlekit.gslides.presentations import PresentationsManager


class ElementsManager:
    """Create and transform page elements on slides."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport
        self._presentations = PresentationsManager(transport)

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
        """Move an element by setting its translation (points → EMU)."""
        require_non_empty(object_id, "object_id")
        tf = AffineTransform.translate_pt(x_pt, y_pt)
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
        """Resize an element via scale factors on a unit size transform.

        Slides sizes are applied through element properties at create time;
        afterward, scaling is done with ``updatePageElementTransform``. This
        helper sets scaleX/scaleY relative to a 1x1 EMU base when using
        ABSOLUTE with explicit size magnitude, which matches common patterns
        of replacing the transform with translate + scale derived from points.
        """
        require_non_empty(object_id, "object_id")
        if width_pt <= 0 or height_pt <= 0:
            raise ValidationError("width_pt and height_pt must be positive")
        # Represent size as scale on a 1 PT identity — use EMU magnitudes as
        # scale relative to 1 EMU so the visual size equals width/height.
        from googlekit.gslides.models import pt_to_emu

        tf = AffineTransform(
            scale_x=float(pt_to_emu(width_pt)),
            scale_y=float(pt_to_emu(height_pt)),
            translate_x_emu=float(pt_to_emu(x_pt or 0.0)),
            translate_y_emu=float(pt_to_emu(y_pt or 0.0)),
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
