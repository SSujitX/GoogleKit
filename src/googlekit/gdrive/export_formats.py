"""Export MIME maps for Google-native Drive files."""

from __future__ import annotations

from googlekit.core.exceptions import ValidationError
from googlekit.core.validation import require_non_empty

# Common short-name → MIME mappings for Google-native export.
EXPORT_MIME_MAP: dict[str, dict[str, str]] = {
    "application/vnd.google-apps.document": {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "odt": "application/vnd.oasis.opendocument.text",
        "rtf": "application/rtf",
        "txt": "text/plain",
        "html": "text/html",
        "epub": "application/epub+zip",
    },
    "application/vnd.google-apps.spreadsheet": {
        "pdf": "application/pdf",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "ods": "application/vnd.oasis.opendocument.spreadsheet",
        "csv": "text/csv",
        "tsv": "text/tab-separated-values",
        "html": "text/html",
    },
    "application/vnd.google-apps.presentation": {
        "pdf": "application/pdf",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "odp": "application/vnd.oasis.opendocument.presentation",
        "txt": "text/plain",
        "png": "image/png",
        "jpeg": "image/jpeg",
    },
    "application/vnd.google-apps.drawing": {
        "pdf": "application/pdf",
        "png": "image/png",
        "jpeg": "image/jpeg",
        "svg": "image/svg+xml",
    },
}


def resolve_export_mime(source_mime: str, export_format: str) -> str:
    """Resolve an export short name or MIME type for a Google-native file.

    Raises:
        ValidationError: When the format is not valid for ``source_mime``.
    """
    require_non_empty(source_mime, "source_mime")
    require_non_empty(export_format, "export_format")
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
