"""Input validation helpers."""

from __future__ import annotations

from pathlib import Path

from googlekit.core.exceptions import ValidationError


def require_non_empty(value: str, name: str) -> str:
    """Require a non-empty string."""
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{name} must be a non-empty string")
    return value


def require_path(path: str | Path, *, must_exist: bool = False) -> Path:
    """Normalize a path and optionally require existence."""
    p = Path(path)
    if must_exist and not p.exists():
        raise ValidationError(f"Path does not exist: {p}")
    return p


def require_positive_int(value: int, name: str) -> int:
    """Require a positive integer."""
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValidationError(f"{name} must be a positive integer")
    return value
