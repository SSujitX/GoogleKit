"""Optional dependency loading helpers."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from googlekit.core.exceptions import MissingExtraError

# Extra name → representative importable module used to detect installation.
_EXTRA_MODULES: dict[str, str] = {
    "gdrive": "googleapiclient.discovery",
    "gsheets": "googleapiclient.discovery",
    "gcalendar": "googleapiclient.discovery",
    "gdocs": "googleapiclient.discovery",
    "gslides": "googleapiclient.discovery",
}

_SERVICE_LABELS: dict[str, str] = {
    "gdrive": "Google Drive",
    "gsheets": "Google Sheets",
    "gcalendar": "Google Calendar",
    "gdocs": "Google Docs",
    "gslides": "Google Slides",
}


def require_extra(extra: str) -> None:
    """Ensure an optional extra's dependencies are importable.

    Args:
        extra: Extra name such as ``gdrive`` or ``gsheets``.

    Raises:
        MissingExtraError: When the required Google client libraries are absent.
        ValueError: When ``extra`` is unknown.
    """
    module_name = _EXTRA_MODULES.get(extra)
    if module_name is None:
        raise ValueError(f"Unknown GoogleKit extra: {extra!r}")
    try:
        import_module(module_name)
    except ImportError as exc:
        label = _SERVICE_LABELS.get(extra, extra)
        raise MissingExtraError(label, extra) from exc


def import_optional(module: str, *, extra: str) -> Any:
    """Import a module, raising MissingExtraError on failure.

    Args:
        module: Fully-qualified module path.
        extra: Extra name for the error message.

    Returns:
        The imported module.
    """
    require_extra(extra)
    return import_module(module)


def installed_extras() -> dict[str, bool]:
    """Return which service extras appear installed."""
    result: dict[str, bool] = {}
    for extra in _EXTRA_MODULES:
        try:
            require_extra(extra)
            result[extra] = True
        except MissingExtraError:
            result[extra] = False
    return result
