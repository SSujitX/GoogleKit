"""Export MIME maps for Google-native Drive files.

Source of truth (verified 2026-07):
https://developers.google.com/workspace/drive/api/guides/ref-export-formats
"""

from __future__ import annotations

from googlekit.core.exceptions import ValidationError
from googlekit.core.validation import require_non_empty

# Document type → short-name → MIME (official Drive exportFormats table).
EXPORT_MIME_MAP: dict[str, dict[str, str]] = {
    "application/vnd.google-apps.document": {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "odt": "application/vnd.oasis.opendocument.text",
        "rtf": "application/rtf",
        "txt": "text/plain",
        # Official table: Web Page (HTML) exports as a zip archive.
        "html": "application/zip",
        "zip": "application/zip",
        "epub": "application/epub+zip",
        "md": "text/markdown",
        "markdown": "text/markdown",
    },
    "application/vnd.google-apps.spreadsheet": {
        "pdf": "application/pdf",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "ods": "application/vnd.oasis.opendocument.spreadsheet",
        "csv": "text/csv",
        "tsv": "text/tab-separated-values",
        # Official table: Web Page (HTML) exports as a zip archive.
        "html": "application/zip",
        "zip": "application/zip",
    },
    "application/vnd.google-apps.presentation": {
        "pdf": "application/pdf",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "odp": "application/vnd.oasis.opendocument.presentation",
        "txt": "text/plain",
        "png": "image/png",
        "jpeg": "image/jpeg",
        "jpg": "image/jpeg",
        "svg": "image/svg+xml",
    },
    "application/vnd.google-apps.drawing": {
        "pdf": "application/pdf",
        "png": "image/png",
        "jpeg": "image/jpeg",
        "jpg": "image/jpeg",
        "svg": "image/svg+xml",
    },
    "application/vnd.google-apps.script": {
        "json": "application/vnd.google-apps.script+json",
    },
}

GOOGLE_VIDS_MIME = "application/vnd.google-apps.vid"


def resolve_export_mime(source_mime: str, export_format: str) -> str:
    """Resolve an export short name or MIME type for a Google-native file.

    Raises:
        ValidationError: When the format is not valid for ``source_mime``.
    """
    require_non_empty(source_mime, "source_mime")
    require_non_empty(export_format, "export_format")
    if source_mime == GOOGLE_VIDS_MIME:
        raise ValidationError(
            "Google Vids cannot be exported with Drive files.export. "
            "Google requires the long-running files.download operation, "
            "which GoogleKit does not currently implement."
        )
    formats = EXPORT_MIME_MAP.get(source_mime)
    if formats is None:
        raise ValidationError(
            f"MIME type {source_mime!r} is not a supported Google-native export type. "
            f"Supported types: {', '.join(sorted(EXPORT_MIME_MAP))}"
        )
    key = export_format.strip().lower().lstrip(".")
    if key in formats:
        return formats[key]
    if export_format in formats.values():
        return export_format
    valid = ", ".join(f"{k} ({v})" for k, v in sorted(formats.items()))
    raise ValidationError(
        f"Invalid export format {export_format!r} for {source_mime}. Valid formats: {valid}"
    )
