"""Slide images manager."""

from __future__ import annotations

from typing import Any

from googlekit.core.exceptions import ValidationError
from googlekit.core.transport import Transport
from googlekit.core.types import PresentationId
from googlekit.core.validation import require_non_empty
from googlekit.gslides.models import AffineTransform, BatchUpdateResult, Size
from googlekit.gslides.presentations import PresentationsManager


class ImagesManager:
    """Insert, replace, and position images on slides."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport
        self._presentations = PresentationsManager(transport)

    def insert_url(
        self,
        presentation_id: PresentationId,
        page_object_id: str,
        url: str,
        *,
        size: Size | None = None,
        transform: AffineTransform | None = None,
        object_id: str | None = None,
        width_pt: float = 300.0,
        height_pt: float = 200.0,
        x_pt: float = 50.0,
        y_pt: float = 50.0,
    ) -> BatchUpdateResult:
        """Insert an image from a publicly accessible URL.

        Args:
            presentation_id: Presentation ID.
            page_object_id: Target slide object ID.
            url: Public image URL.
            size: Optional size in EMUs.
            transform: Optional transform.
            object_id: Optional stable object ID.
            width_pt: Default width when ``size`` omitted.
            height_pt: Default height when ``size`` omitted.
            x_pt: Default X position in points.
            y_pt: Default Y position in points.
        """
        require_non_empty(page_object_id, "page_object_id")
        require_non_empty(url, "url")
        sz = size or Size.from_pt(width_pt, height_pt)
        tf = transform or AffineTransform.translate_pt(x_pt, y_pt)
        element: dict[str, Any] = {
            "pageObjectId": page_object_id,
            "size": sz.to_api(),
            "transform": tf.to_api(),
        }
        create: dict[str, Any] = {
            "url": url,
            "elementProperties": element,
        }
        if object_id:
            create["objectId"] = object_id
        return self._presentations.batch_update(
            presentation_id,
            [{"createImage": create}],
        )

    def replace(
        self,
        presentation_id: PresentationId,
        image_object_id: str,
        url: str,
        *,
        image_replace_method: str = "CENTER_INSIDE",
    ) -> BatchUpdateResult:
        """Replace an existing image's content by object ID."""
        require_non_empty(image_object_id, "image_object_id")
        require_non_empty(url, "url")
        return self._presentations.batch_update(
            presentation_id,
            [
                {
                    "replaceImage": {
                        "imageObjectId": image_object_id,
                        "url": url,
                        "imageReplaceMethod": image_replace_method,
                    }
                }
            ],
        )

    def position_and_size(
        self,
        presentation_id: PresentationId,
        object_id: str,
        *,
        x_pt: float,
        y_pt: float,
        width_pt: float,
        height_pt: float,
        apply_mode: str = "ABSOLUTE",
    ) -> BatchUpdateResult:
        """Set image position and size via an absolute transform.

        Scale is expressed in EMUs so a 1x1 EMU source maps to the target size.
        """
        require_non_empty(object_id, "object_id")
        if width_pt <= 0 or height_pt <= 0:
            raise ValidationError("width_pt and height_pt must be positive")
        from googlekit.gslides.models import pt_to_emu

        tf = AffineTransform(
            scale_x=float(pt_to_emu(width_pt)),
            scale_y=float(pt_to_emu(height_pt)),
            translate_x_emu=float(pt_to_emu(x_pt)),
            translate_y_emu=float(pt_to_emu(y_pt)),
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
