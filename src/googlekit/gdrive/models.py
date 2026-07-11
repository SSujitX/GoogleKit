"""Typed models for Google Drive resources."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from googlekit.core.constants import DRIVE_FOLDER_MIME

FILE_FIELDS = (
    "id, name, mimeType, parents, size, md5Checksum, sha1Checksum, sha256Checksum, "
    "trashed, starred, shared, webViewLink, webContentLink, createdTime, "
    "modifiedTime, owners, driveId, shortcutDetails, capabilities"
)
PERMISSION_FIELDS = "id, type, role, emailAddress, displayName, domain, allowFileDiscovery"
CHANGE_FIELDS = (
    "nextPageToken, newStartPageToken, "
    "changes(changeType, removed, fileId, time, file(" + FILE_FIELDS + "))"
)


class OverwritePolicy(StrEnum):
    """Behavior when a destination name already exists."""

    ERROR = "error"
    SKIP = "skip"
    OVERWRITE = "overwrite"


class PermissionRole(StrEnum):
    """Roles accepted by sharing helpers (Drive Permission resource)."""

    OWNER = "owner"
    ORGANIZER = "organizer"
    FILE_ORGANIZER = "fileOrganizer"
    WRITER = "writer"
    COMMENTER = "commenter"
    READER = "reader"


@dataclass(slots=True)
class DriveFile:
    """Google Drive file (or folder) metadata."""

    id: str
    name: str
    mime_type: str | None = None
    parents: list[str] = field(default_factory=list)
    size: int | None = None
    md5_checksum: str | None = None
    sha1_checksum: str | None = None
    sha256_checksum: str | None = None
    trashed: bool = False
    starred: bool = False
    shared: bool = False
    web_view_link: str | None = None
    web_content_link: str | None = None
    created_time: str | None = None
    modified_time: str | None = None
    drive_id: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> DriveFile:
        size_raw = data.get("size")
        size = int(size_raw) if size_raw is not None else None
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            mime_type=data.get("mimeType"),
            parents=list(data.get("parents") or []),
            size=size,
            md5_checksum=data.get("md5Checksum"),
            sha1_checksum=data.get("sha1Checksum"),
            sha256_checksum=data.get("sha256Checksum"),
            trashed=bool(data.get("trashed", False)),
            starred=bool(data.get("starred", False)),
            shared=bool(data.get("shared", False)),
            web_view_link=data.get("webViewLink"),
            web_content_link=data.get("webContentLink"),
            created_time=data.get("createdTime"),
            modified_time=data.get("modifiedTime"),
            drive_id=data.get("driveId"),
            raw=dict(data),
        )

    @property
    def is_folder(self) -> bool:
        return self.mime_type == DRIVE_FOLDER_MIME

    @property
    def is_google_native(self) -> bool:
        return bool(
            self.mime_type
            and self.mime_type.startswith("application/vnd.google-apps.")
            and self.mime_type != DRIVE_FOLDER_MIME
            and self.mime_type != "application/vnd.google-apps.shortcut"
        )


@dataclass(slots=True)
class DriveFolder:
    """Google Drive folder metadata."""

    id: str
    name: str
    parents: list[str] = field(default_factory=list)
    trashed: bool = False
    shared: bool = False
    web_view_link: str | None = None
    created_time: str | None = None
    modified_time: str | None = None
    drive_id: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> DriveFolder:
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            parents=list(data.get("parents") or []),
            trashed=bool(data.get("trashed", False)),
            shared=bool(data.get("shared", False)),
            web_view_link=data.get("webViewLink"),
            created_time=data.get("createdTime"),
            modified_time=data.get("modifiedTime"),
            drive_id=data.get("driveId"),
            raw=dict(data),
        )

    @classmethod
    def from_file(cls, file: DriveFile) -> DriveFolder:
        return cls(
            id=file.id,
            name=file.name,
            parents=list(file.parents),
            trashed=file.trashed,
            shared=file.shared,
            web_view_link=file.web_view_link,
            created_time=file.created_time,
            modified_time=file.modified_time,
            drive_id=file.drive_id,
            raw=dict(file.raw),
        )


@dataclass(slots=True)
class Permission:
    """Drive permission entry."""

    id: str
    type: str
    role: str
    email_address: str | None = None
    display_name: str | None = None
    domain: str | None = None
    allow_file_discovery: bool | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Permission:
        return cls(
            id=str(data.get("id", "")),
            type=str(data.get("type", "")),
            role=str(data.get("role", "")),
            email_address=data.get("emailAddress"),
            display_name=data.get("displayName"),
            domain=data.get("domain"),
            allow_file_discovery=data.get("allowFileDiscovery"),
            raw=dict(data),
        )


@dataclass(slots=True)
class Change:
    """A single change from the Drive changes feed."""

    change_type: str | None = None
    file_id: str | None = None
    removed: bool = False
    time: str | None = None
    file: DriveFile | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Change:
        file_data = data.get("file")
        return cls(
            change_type=data.get("changeType"),
            file_id=data.get("fileId"),
            removed=bool(data.get("removed", False)),
            time=data.get("time"),
            file=DriveFile.from_api(file_data) if isinstance(file_data, dict) else None,
            raw=dict(data),
        )


@dataclass(slots=True)
class UploadResult:
    """Result of an upload operation."""

    file: DriveFile
    bytes_uploaded: int | None = None
    overwritten: bool = False
    raw: dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass(slots=True)
class DownloadResult:
    """Result of a download or export operation."""

    size: int = 0
    path: Path | None = None
    mime_type: str | None = None
    exported: bool = False
    data: bytes | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)


def shared_drive_params(
    supports_all_drives: bool,
    *,
    list_mode: bool = False,
) -> dict[str, bool]:
    """Build supportsAllDrives kwargs when Shared Drive support is enabled."""
    if not supports_all_drives:
        return {}
    params: dict[str, bool] = {"supportsAllDrives": True}
    if list_mode:
        params["includeItemsFromAllDrives"] = True
    return params
