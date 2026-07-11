"""Extensive unit tests for Docs UTF-16 index helpers."""

from __future__ import annotations

import pytest

from googlekit.core.exceptions import ValidationError
from googlekit.gdocs.utf16 import (
    offset_utf16,
    py_index_to_utf16,
    py_slice_to_utf16_range,
    utf16_index_to_py,
    utf16_len,
    utf16_range_to_py_slice,
)

EMOJI = "\U0001f600"  # 😀 GRINNING FACE — one code point, two UTF-16 units
MUSICAL = "\U0001d11e"  # 𝄞 — supplementary plane
CJK_BMP = "字"  # BMP CJK — one UTF-16 unit


def test_utf16_len_ascii() -> None:
    assert utf16_len("") == 0
    assert utf16_len("hello") == 5
    assert utf16_len("Hi there") == 8


def test_utf16_len_emoji() -> None:
    assert utf16_len(EMOJI) == 2
    assert len(EMOJI) == 1
    assert utf16_len(f"A{EMOJI}B") == 4
    assert len(f"A{EMOJI}B") == 3


def test_utf16_len_mixed_bmp_and_supplementary() -> None:
    text = f"Hi {EMOJI} {CJK_BMP} {MUSICAL}"
    # H i space 😀(2) space 字(1) space 𝄞(2) = 1+1+1+2+1+1+1+2 = 10
    assert utf16_len(text) == 10
    assert len(text) == 8


def test_py_index_to_utf16_before_after_emoji() -> None:
    text = f"A{EMOJI}B"
    assert py_index_to_utf16(text, 0) == 0
    assert py_index_to_utf16(text, 1) == 1  # after A
    assert py_index_to_utf16(text, 2) == 3  # after emoji (2 units)
    assert py_index_to_utf16(text, 3) == 4  # end


def test_py_index_to_utf16_end_inclusive() -> None:
    text = "abc"
    assert py_index_to_utf16(text, len(text)) == 3


def test_py_index_to_utf16_out_of_range() -> None:
    with pytest.raises(ValidationError):
        py_index_to_utf16("ab", -1)
    with pytest.raises(ValidationError):
        py_index_to_utf16("ab", 3)
    with pytest.raises(ValidationError):
        py_index_to_utf16("ab", True)  # type: ignore[arg-type]


def test_utf16_index_to_py_roundtrip() -> None:
    text = f"Hi {EMOJI}!"
    for py_i in range(len(text) + 1):
        u16 = py_index_to_utf16(text, py_i)
        assert utf16_index_to_py(text, u16) == py_i


def test_utf16_index_to_py_inside_surrogate_pair() -> None:
    text = f"X{EMOJI}Y"
    # UTF-16 layout: X(1), high, low, Y(1) → units 0,1,2,3,4
    # Index 2 is the low surrogate — invalid boundary for Python mapping.
    with pytest.raises(ValidationError, match="surrogate"):
        utf16_index_to_py(text, 2)


def test_utf16_index_to_py_out_of_range() -> None:
    with pytest.raises(ValidationError):
        utf16_index_to_py("a", -1)
    with pytest.raises(ValidationError):
        utf16_index_to_py("a", 5)


def test_py_slice_to_utf16_range() -> None:
    text = f"ab{EMOJI}cd"
    start, end = py_slice_to_utf16_range(text, 2, 4)
    # py [2:4] is emoji + 'c' → utf16 width 2+1 = 3 units starting at 2
    assert start == 2
    assert end == 5


def test_py_slice_invalid() -> None:
    with pytest.raises(ValidationError):
        py_slice_to_utf16_range("abc", 2, 1)


def test_utf16_range_to_py_slice() -> None:
    text = f"ab{EMOJI}cd"
    py_start, py_end = utf16_range_to_py_slice(text, 2, 5)
    assert text[py_start:py_end] == f"{EMOJI}c"


def test_offset_utf16() -> None:
    assert offset_utf16(1, "Hello") == 6
    assert offset_utf16(1, EMOJI) == 3
    with pytest.raises(ValidationError):
        offset_utf16(-1, "x")


def test_docs_body_style_span_example() -> None:
    """Simulate insert-at-1 then style the inserted span using UTF-16 length."""
    insertion_index = 1
    text = f"Hello {EMOJI}"
    end = offset_utf16(insertion_index, text)
    assert end == 1 + utf16_len(text)
    assert end == 1 + 5 + 1 + 2  # Hello + space + emoji


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", 0),
        ("a", 1),
        ("é", 1),  # BMP Latin-1
        ("日本語", 3),
        (EMOJI, 2),
        (EMOJI + EMOJI, 4),
        ("👨‍👩‍👧‍👦", utf16_len("👨‍👩‍👧‍👦")),  # ZWJ family
    ],
)
def test_utf16_len_parametrized(text: str, expected: int) -> None:
    assert utf16_len(text) == expected
    # Family emoji: verify it differs from Python len when ZWJ sequences present
    if text == "👨‍👩‍👧‍👦":
        assert utf16_len(text) > len(text)
