"""Validation helper tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from googlekit.core.exceptions import ValidationError
from googlekit.core.validation import require_non_empty, require_path, require_positive_int


def test_require_non_empty() -> None:
    assert require_non_empty("abc", "name") == "abc"
    with pytest.raises(ValidationError, match="non-empty"):
        require_non_empty("", "name")
    with pytest.raises(ValidationError):
        require_non_empty("   ", "name")


def test_require_path(tmp_path: Path) -> None:
    p = require_path(tmp_path / "x.txt")
    assert isinstance(p, Path)
    with pytest.raises(ValidationError, match="does not exist"):
        require_path(tmp_path / "missing.txt", must_exist=True)
    existing = tmp_path / "ok.txt"
    existing.write_text("x", encoding="utf-8")
    assert require_path(existing, must_exist=True) == existing


def test_require_positive_int() -> None:
    assert require_positive_int(3, "n") == 3
    with pytest.raises(ValidationError):
        require_positive_int(0, "n")
    with pytest.raises(ValidationError):
        require_positive_int(-1, "n")
    with pytest.raises(ValidationError):
        require_positive_int(True, "n")  # type: ignore[arg-type]
