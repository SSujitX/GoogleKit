"""Google Slides API package."""

from __future__ import annotations

from googlekit.gslides.client import SlidesClient
from googlekit.gslides.models import (
    AffineTransform,
    BatchUpdateResult,
    PageElement,
    ParagraphStyle,
    PredefinedLayout,
    Presentation,
    ShapeType,
    Size,
    SlidePage,
    TextStyle,
    inches_to_emu,
    pt_to_emu,
)

__all__ = [
    "AffineTransform",
    "BatchUpdateResult",
    "PageElement",
    "ParagraphStyle",
    "PredefinedLayout",
    "Presentation",
    "ShapeType",
    "Size",
    "SlidePage",
    "SlidesClient",
    "TextStyle",
    "inches_to_emu",
    "pt_to_emu",
]
