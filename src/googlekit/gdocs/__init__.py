"""Google Docs API package."""

from __future__ import annotations

from googlekit.gdocs.client import DocsClient
from googlekit.gdocs.models import (
    BatchUpdateResult,
    BulletPreset,
    Document,
    NamedStyleType,
    ParagraphStyle,
    StructuralElement,
    TextRange,
    TextStyle,
)
from googlekit.gdocs.utf16 import (
    offset_utf16,
    py_index_to_utf16,
    py_slice_to_utf16_range,
    utf16_index_to_py,
    utf16_len,
    utf16_range_to_py_slice,
)

__all__ = [
    "BatchUpdateResult",
    "BulletPreset",
    "DocsClient",
    "Document",
    "NamedStyleType",
    "ParagraphStyle",
    "StructuralElement",
    "TextRange",
    "TextStyle",
    "offset_utf16",
    "py_index_to_utf16",
    "py_slice_to_utf16_range",
    "utf16_index_to_py",
    "utf16_len",
    "utf16_range_to_py_slice",
]
