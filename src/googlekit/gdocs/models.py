"""Typed models for Google Docs."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class NamedStyleType(StrEnum):
    """Built-in paragraph named styles (headings)."""

    NORMAL_TEXT = "NORMAL_TEXT"
    TITLE = "TITLE"
    SUBTITLE = "SUBTITLE"
    HEADING_1 = "HEADING_1"
    HEADING_2 = "HEADING_2"
    HEADING_3 = "HEADING_3"
    HEADING_4 = "HEADING_4"
    HEADING_5 = "HEADING_5"
    HEADING_6 = "HEADING_6"


class BulletPreset(StrEnum):
    """Common Docs bullet / numbered-list presets."""

    BULLET_DISC_CIRCLE_SQUARE = "BULLET_DISC_CIRCLE_SQUARE"
    BULLET_DIAMONDX_ARROW3D_SQUARE = "BULLET_DIAMONDX_ARROW3D_SQUARE"
    BULLET_CHECKBOX = "BULLET_CHECKBOX"
    NUMBERED_DECIMAL_ALPHA_ROMAN = "NUMBERED_DECIMAL_ALPHA_ROMAN"
    NUMBERED_DECIMAL_NESTED = "NUMBERED_DECIMAL_NESTED"


@dataclass(slots=True)
class TextStyle:
    """Subset of Docs TextStyle fields for updates."""

    bold: bool | None = None
    italic: bool | None = None
    underline: bool | None = None
    strikethrough: bool | None = None
    font_size_pt: float | None = None
    font_family: str | None = None
    foreground_color: dict[str, Any] | None = None
    background_color: dict[str, Any] | None = None
    link_url: str | None = None

    def to_api(self) -> tuple[dict[str, Any], str]:
        """Return ``(textStyle dict, fields mask)``."""
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
        if self.strikethrough is not None:
            style["strikethrough"] = self.strikethrough
            fields.append("strikethrough")
        if self.font_size_pt is not None:
            style["fontSize"] = {"magnitude": self.font_size_pt, "unit": "PT"}
            fields.append("fontSize")
        if self.font_family is not None:
            style["weightedFontFamily"] = {"fontFamily": self.font_family}
            fields.append("weightedFontFamily")
        if self.foreground_color is not None:
            style["foregroundColor"] = self.foreground_color
            fields.append("foregroundColor")
        if self.background_color is not None:
            style["backgroundColor"] = self.background_color
            fields.append("backgroundColor")
        if self.link_url is not None:
            style["link"] = {"url": self.link_url}
            fields.append("link")
        return style, ",".join(fields)


@dataclass(slots=True)
class ParagraphStyle:
    """Subset of Docs ParagraphStyle fields for updates."""

    named_style_type: NamedStyleType | str | None = None
    alignment: str | None = None
    line_spacing: float | None = None
    space_above_pt: float | None = None
    space_below_pt: float | None = None
    indent_start_pt: float | None = None
    indent_first_line_pt: float | None = None

    def to_api(self) -> tuple[dict[str, Any], str]:
        """Return ``(paragraphStyle dict, fields mask)``."""
        style: dict[str, Any] = {}
        fields: list[str] = []
        if self.named_style_type is not None:
            style["namedStyleType"] = str(self.named_style_type)
            fields.append("namedStyleType")
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
        if self.indent_start_pt is not None:
            style["indentStart"] = {"magnitude": self.indent_start_pt, "unit": "PT"}
            fields.append("indentStart")
        if self.indent_first_line_pt is not None:
            style["indentFirstLine"] = {
                "magnitude": self.indent_first_line_pt,
                "unit": "PT",
            }
            fields.append("indentFirstLine")
        return style, ",".join(fields)


@dataclass(slots=True)
class TextRange:
    """A UTF-16 index range within a document segment."""

    start_index: int
    end_index: int
    segment_id: str | None = None

    def to_api(self) -> dict[str, Any]:
        rng: dict[str, Any] = {
            "startIndex": self.start_index,
            "endIndex": self.end_index,
        }
        if self.segment_id:
            rng["segmentId"] = self.segment_id
        return rng


@dataclass(slots=True)
class StructuralElement:
    """One structural element from a document body (or other segment)."""

    start_index: int | None
    end_index: int | None
    kind: str
    text: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> StructuralElement:
        kind = "unknown"
        text: str | None = None
        if "paragraph" in data:
            kind = "paragraph"
            runs = (data.get("paragraph") or {}).get("elements") or []
            parts: list[str] = []
            for run in runs:
                tr = run.get("textRun")
                if tr and "content" in tr:
                    parts.append(str(tr["content"]))
            text = "".join(parts) if parts else None
        elif "table" in data:
            kind = "table"
        elif "tableOfContents" in data:
            kind = "tableOfContents"
        elif "sectionBreak" in data:
            kind = "sectionBreak"
        return cls(
            start_index=data.get("startIndex"),
            end_index=data.get("endIndex"),
            kind=kind,
            text=text,
            raw=data,
        )


@dataclass(slots=True)
class Document:
    """Google Docs document metadata and body structure."""

    id: str
    title: str
    revision_id: str | None = None
    body_end_index: int | None = None
    structural_elements: list[StructuralElement] = field(default_factory=list)
    named_ranges: dict[str, list[TextRange]] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Document:
        body = data.get("body") or {}
        elements = [StructuralElement.from_api(el) for el in body.get("content") or []]
        end_index: int | None = None
        if elements and elements[-1].end_index is not None:
            end_index = elements[-1].end_index

        named: dict[str, list[TextRange]] = {}
        for name, nr in (data.get("namedRanges") or {}).items():
            ranges: list[TextRange] = []
            for item in nr.get("namedRanges") or []:
                for r in item.get("ranges") or []:
                    ranges.append(
                        TextRange(
                            start_index=int(r.get("startIndex", 0)),
                            end_index=int(r.get("endIndex", 0)),
                            segment_id=r.get("segmentId"),
                        )
                    )
            named[name] = ranges

        return cls(
            id=str(data.get("documentId", "")),
            title=str(data.get("title", "")),
            revision_id=data.get("revisionId"),
            body_end_index=end_index,
            structural_elements=elements,
            named_ranges=named,
            raw=data,
        )

    @property
    def plain_text(self) -> str:
        """Concatenate paragraph text from the body (best-effort)."""
        parts: list[str] = []
        for el in self.structural_elements:
            if el.text is not None:
                parts.append(el.text)
        return "".join(parts)


@dataclass(slots=True)
class BatchUpdateResult:
    """Result of a documents.batchUpdate call."""

    document_id: str
    replies: list[dict[str, Any]] = field(default_factory=list)
    write_control: dict[str, Any] | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> BatchUpdateResult:
        return cls(
            document_id=str(data.get("documentId", "")),
            replies=list(data.get("replies") or []),
            write_control=data.get("writeControl"),
            raw=data,
        )
