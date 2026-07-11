"""Shared constants."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version


def package_version() -> str:
    """Return installed package version from metadata (``pyproject.toml``).

    Falls back to ``dev`` only when the package is not installed (rare local
    import). Bump version in ``pyproject.toml`` only — do not hardcode here.
    """
    try:
        return version("googlekit")
    except PackageNotFoundError:  # pragma: no cover
        return "dev"


USER_AGENT = f"googlekit/{package_version()}"
DEFAULT_PAGE_SIZE = 100
DEFAULT_MAX_RETRIES = 5
DEFAULT_CHUNK_SIZE = 256 * 1024  # 256 KiB for resumable uploads
DRIVE_FOLDER_MIME = "application/vnd.google-apps.folder"
DRIVE_SHORTCUT_MIME = "application/vnd.google-apps.shortcut"
