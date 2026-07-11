"""UTF-16 index helpers for the Google Docs API.

The Docs API measures all document indexes in **UTF-16 code units**, not Python
string indexes (Unicode code points) and not UTF-8 bytes.

Why this matters
----------------
Characters in the Basic Multilingual Plane (BMP, U+0000-U+FFFF) occupy **one**
UTF-16 code unit. Characters outside the BMP (for example many emoji and some
CJK ideographs) are encoded as a surrogate pair and occupy **two** UTF-16 code
units.

Python 3 ``str`` indexes count Unicode code points, so::

    text = "Hi 😄"
    len(text)           # 4  (H, i, space, grinning-face)
    utf16_len(text)     # 5  (H, i, space, high-surrogate, low-surrogate)

Always convert Python indexes with these helpers before calling Docs API
``location.index``, ``range.startIndex``, or ``range.endIndex``.

Body content in a new document typically starts at UTF-16 index ``1`` (index
``0`` is reserved for the document segment start).
"""

from __future__ import annotations

from googlekit.core.exceptions import ValidationError


def utf16_len(text: str) -> int:
    """Return the length of ``text`` in UTF-16 code units.

    Args:
        text: Arbitrary Unicode string.

    Returns:
        Number of UTF-16 code units (surrogate pairs count as two).
    """
    return sum(2 if ord(ch) > 0xFFFF else 1 for ch in text)


def py_index_to_utf16(text: str, index: int) -> int:
    """Convert a Python ``str`` index into a UTF-16 code-unit index.

    Args:
        text: The string the index refers to (for example plain body text).
        index: Python index in ``[0, len(text)]`` (end-inclusive for append).

    Returns:
        Equivalent UTF-16 code-unit offset from the start of ``text``.

    Raises:
        ValidationError: When ``index`` is out of range.
    """
    if not isinstance(index, int) or isinstance(index, bool):
        raise ValidationError("index must be an int")
    if index < 0 or index > len(text):
        raise ValidationError(
            f"Python index {index} is out of range for text of length {len(text)}"
        )
    return utf16_len(text[:index])


def utf16_index_to_py(text: str, utf16_index: int) -> int:
    """Convert a UTF-16 code-unit index into a Python ``str`` index.

    Args:
        text: The string the index refers to.
        utf16_index: UTF-16 offset in ``[0, utf16_len(text)]``.

    Returns:
        Equivalent Python code-point index.

    Raises:
        ValidationError: When ``utf16_index`` is out of range or lands in the
            middle of a surrogate pair.
    """
    if not isinstance(utf16_index, int) or isinstance(utf16_index, bool):
        raise ValidationError("utf16_index must be an int")
    if utf16_index < 0:
        raise ValidationError(f"utf16_index {utf16_index} must be >= 0")

    units = 0
    for i, ch in enumerate(text):
        if units == utf16_index:
            return i
        width = 2 if ord(ch) > 0xFFFF else 1
        if units + width > utf16_index:
            raise ValidationError(
                f"utf16_index {utf16_index} falls inside a surrogate pair "
                f"at Python index {i} (character U+{ord(ch):04X})"
            )
        units += width

    if units == utf16_index:
        return len(text)
    raise ValidationError(
        f"utf16_index {utf16_index} is out of range for text with {units} UTF-16 code units"
    )


def py_slice_to_utf16_range(text: str, start: int, end: int) -> tuple[int, int]:
    """Convert a Python half-open slice ``[start, end)`` to UTF-16 indexes.

    Args:
        text: Source string.
        start: Python start index (inclusive).
        end: Python end index (exclusive).

    Returns:
        ``(utf16_start, utf16_end)`` suitable for Docs ``Range`` fields.

    Raises:
        ValidationError: When the slice is invalid.
    """
    if start > end:
        raise ValidationError(f"start ({start}) must be <= end ({end})")
    return py_index_to_utf16(text, start), py_index_to_utf16(text, end)


def utf16_range_to_py_slice(text: str, utf16_start: int, utf16_end: int) -> tuple[int, int]:
    """Convert a UTF-16 half-open range to a Python slice ``[start, end)``.

    Args:
        text: Source string.
        utf16_start: UTF-16 start (inclusive).
        utf16_end: UTF-16 end (exclusive).

    Returns:
        ``(py_start, py_end)``.
    """
    if utf16_start > utf16_end:
        raise ValidationError(f"utf16_start ({utf16_start}) must be <= utf16_end ({utf16_end})")
    return utf16_index_to_py(text, utf16_start), utf16_index_to_py(text, utf16_end)


def offset_utf16(base_utf16: int, text: str) -> int:
    """Return ``base_utf16 + utf16_len(text)``.

    Useful when inserting text and computing the new end index for styling.
    """
    if base_utf16 < 0:
        raise ValidationError("base_utf16 must be >= 0")
    return base_utf16 + utf16_len(text)
