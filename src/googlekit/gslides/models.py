"""Typed models for Google Slides."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from googlekit.core.exceptions import ValidationError


class PredefinedLayout(StrEnum):
    """Common Slides predefined layouts."""

    BLANK = "BLANK"
    CAPTION_ONLY = "CAPTION_ONLY"
    TITLE = "TITLE"
    TITLE_AND_BODY = "TITLE_AND_BODY"
    TITLE_AND_TWO_COLUMNS = "TITLE_AND_TWO_COLUMNS"
    TITLE_ONLY = "TITLE_ONLY"
    SECTION_HEADER = "SECTION_HEADER"
    SECTION_TITLE_AND_DESCRIPTION = "SECTION_TITLE_AND_DESCRIPTION"
    ONE_COLUMN_TEXT = "ONE_COLUMN_TEXT"
    MAIN_POINT = "MAIN_POINT"
    BIG_NUMBER = "BIG_NUMBER"


class ShapeType(StrEnum):
    """Common shape types for createShape."""

    TEXT_BOX = "TEXT_BOX"
    RECTANGLE = "RECTANGLE"
    ROUND_RECTANGLE = "ROUND_RECTANGLE"
    ELLIPSE = "ELLIPSE"
    TRIANGLE = "TRIANGLE"
    RIGHT_TRIANGLE = "RIGHT_TRIANGLE"
    DIAMOND = "DIAMOND"


class Unit(StrEnum):
    """Slides size / transform units."""

    EMU = "EMU"
    PT = "PT"


# 1 inch = 914400 EMUs; 1 point = 12700 EMUs
EMU_PER_PT = 12700
EMU_PER_INCH = 914400


def pt_to_emu(pt: float) -> int:
    """Convert points to English Metric Units."""
    return round(pt * EMU_PER_PT)


def inches_to_emu(inches: float) -> int:
    """Convert inches to English Metric Units."""
    return round(inches * EMU_PER_INCH)


@dataclass(slots=True)
class Size:
    """Width/height in EMUs (or convert from points)."""

    width_emu: int
    height_emu: int

    @classmethod
    def from_pt(cls, width_pt: float, height_pt: float) -> Size:
        if width_pt <= 0 or height_pt <= 0:
            raise ValidationError("width_pt and height_pt must be positive")
        return cls(pt_to_emu(width_pt), pt_to_emu(height_pt))

    @classmethod
    def from_inches(cls, width_in: float, height_in: float) -> Size:
        if width_in <= 0 or height_in <= 0:
            raise ValidationError("width_in and height_in must be positive")
        return cls(inches_to_emu(width_in), inches_to_emu(height_in))

    def to_api(self) -> dict[str, Any]:
        return {
            "width": {"magnitude": self.width_emu, "unit": "EMU"},
            "height": {"magnitude": self.height_emu, "unit": "EMU"},
        }


@dataclass(slots=True)
class AffineTransform:
    """2D affine transform in EMUs (translation) / scale."""

    scale_x: float = 1.0
    scale_y: float = 1.0
    shear_x: float = 0.0
    shear_y: float = 0.0
    translate_x_emu: float = 0.0
    translate_y_emu: float = 0.0
    unit: str = "EMU"

    def to_api(self) -> dict[str, Any]:
        return {
            "scaleX": self.scale_x,
            "scaleY": self.scale_y,
            "shearX": self.shear_x,
            "shearY": self.shear_y,
            "translateX": self.translate_x_emu,
            "translateY": self.translate_y_emu,
            "unit": self.unit,
        }

    @classmethod
    def translate_pt(cls, x_pt: float, y_pt: float) -> AffineTransform:
        return cls(
            translate_x_emu=float(pt_to_emu(x_pt)),
            translate_y_emu=float(pt_to_emu(y_pt)),
        )


@dataclass(slots=True)
class TextStyle:
    """Subset of Slides TextStyle fields."""

    bold: bool | None = None
    italic: bool | None = None
    underline: bool | None = None
    font_size_pt: float | None = None
    font_family: str | None = None
    foreground_color: dict[str, Any] | None = None

    def to_api(self) -> tuple[dict[str, Any], str]:
        style: dict[str, Any] = {}
        fields: list[str] = []
        if self.bold is not None:
            style["bold"] = self.bold
            fields.append("bold")
        if self.italic is not None:
            style["italic"] = self.italic
            fields.append("italic")
        if self.underline is not None:
            style["underline"] = self.underline
            fields.append("underline")
        if self.font_size_pt is not None:
            style["fontSize"] = {"magnitude": self.font_size_pt, "unit": "PT"}
            fields.append("fontSize")
        if self.font_family is not None:
            style["fontFamily"] = self.font_family
            fields.append("fontFamily")
        if self.foreground_color is not None:
            style["foregroundColor"] = self.foreground_color
            fields.append("foregroundColor")
        return style, ",".join(fields)


@dataclass(slots=True)
class ParagraphStyle:
    """Subset of Slides ParagraphStyle fields."""

    alignment: str | None = None
    line_spacing: float | None = None
    space_above_pt: float | None = None
    space_below_pt: float | None = None

    def to_api(self) -> tuple[dict[str, Any], str]:
        style: dict[str, Any] = {}
        fields: list[str] = []
        if self.alignment is not None:
            style["alignment"] = self.alignment
            fields.append("alignment")
        if self.line_spacing is not None:
            style["lineSpacing"] = self.line_spacing
            fields.append("lineSpacing")
        if self.space_above_pt is not None:
            style["spaceAbove"] = {"magnitude": self.space_above_pt, "unit": "PT"}
            fields.append("spaceAbove")
        if self.space_below_pt is not None:
            style["spaceBelow"] = {"magnitude": self.space_below_pt, "unit": "PT"}
            fields.append("spaceBelow")
        return style, ",".join(fields)


@dataclass(slots=True)
class PageElement:
    """A page element (shape, image, table, …) on a slide."""

    object_id: str
    size: Size | None = None
    transform: AffineTransform | None = None
    kind: str = "unknown"
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> PageElement:
        kind = "unknown"
        for key in (
            "shape",
            "image",
            "table",
            "line",
            "video",
            "sheetsChart",
            "wordArt",
            "group",
        ):
            if key in data:
                kind = key
                break
        size = None
        if "size" in data:
            sz = data["size"]
            w = (sz.get("width") or {}).get("magnitude", 0)
            h = (sz.get("height") or {}).get("magnitude", 0)
            size = Size(int(w), int(h))
        transform = None
        if "transform" in data:
            t = data["transform"]
            transform = AffineTransform(
                scale_x=float(t.get("scaleX", 1)),
                scale_y=float(t.get("scaleY", 1)),
                shear_x=float(t.get("shearX", 0)),
                shear_y=float(t.get("shearY", 0)),
                translate_x_emu=float(t.get("translateX", 0)),
                translate_y_emu=float(t.get("translateY", 0)),
                unit=str(t.get("unit", "EMU")),
            )
        return cls(
            object_id=str(data.get("objectId", "")),
            size=size,
            transform=transform,
            kind=kind,
            raw=data,
        )


@dataclass(slots=True)
class SlidePage:
    """A single slide (page) in a presentation."""

    object_id: str
    layout_object_id: str | None = None
    elements: list[PageElement] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> SlidePage:
        props = data.get("slideProperties") or {}
        elements = [PageElement.from_api(el) for el in data.get("pageElements") or []]
        return cls(
            object_id=str(data.get("objectId", "")),
            layout_object_id=props.get("layoutObjectId"),
            elements=elements,
            raw=data,
        )


@dataclass(slots=True)
class Presentation:
    """Google Slides presentation metadata and pages."""

    id: str
    title: str
    slides: list[SlidePage] = field(default_factory=list)
    page_size: Size | None = None
    revision_id: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Presentation:
        slides = [SlidePage.from_api(s) for s in data.get("slides") or []]
        page_size = None
        if "pageSize" in data:
            ps = data["pageSize"]
            page_size = Size(
                int((ps.get("width") or {}).get("magnitude", 0)),
                int((ps.get("height") or {}).get("magnitude", 0)),
            )
        return cls(
            id=str(data.get("presentationId", "")),
            title=str(data.get("title", "")),
            slides=slides,
            page_size=page_size,
            revision_id=data.get("revisionId"),
            raw=data,
        )

    def slide_ids(self) -> list[str]:
        return [s.object_id for s in self.slides]


@dataclass(slots=True)
class BatchUpdateResult:
    """Result of a presentations.batchUpdate call."""

    presentation_id: str
    replies: list[dict[str, Any]] = field(default_factory=list)
    write_control: dict[str, Any] | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> BatchUpdateResult:
        return cls(
            presentation_id=str(data.get("presentationId", "")),
            replies=list(data.get("replies") or []),
            write_control=data.get("writeControl"),
            raw=data,
        )
