"""Shared constants."""

from __future__ import annotations

USER_AGENT = "googlekit/0.1.0"
DEFAULT_PAGE_SIZE = 100
DEFAULT_MAX_RETRIES = 5
DEFAULT_CHUNK_SIZE = 256 * 1024  # 256 KiB for resumable uploads
DRIVE_FOLDER_MIME = "application/vnd.google-apps.folder"
DRIVE_SHORTCUT_MIME = "application/vnd.google-apps.shortcut"
