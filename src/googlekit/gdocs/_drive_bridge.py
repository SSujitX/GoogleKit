"""Helpers that bridge Docs/Slides operations to Google Drive.

Export and sharing for Docs and Slides are Drive API operations. These helpers
never silently broaden OAuth scopes: callers must already hold Drive scopes and
install the ``gdrive`` extra.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from googlekit.auth.scopes import Scope, ScopeSet
from googlekit.core.configuration import ClientConfig
from googlekit.core.exceptions import InsufficientScopesError, ValidationError
from googlekit.core.optional import require_extra
from googlekit.core.protocols import CredentialProvider
from googlekit.core.transport import Transport
from googlekit.core.validation import require_non_empty

# Scopes that can read/export Google-native files.
_EXPORT_SCOPES = ScopeSet.of(
    Scope.DRIVE,
    Scope.DRIVE_READONLY,
    Scope.DRIVE_FILE,
)

# Scopes that can create permissions (share).
_SHARE_SCOPES = ScopeSet.of(
    Scope.DRIVE,
    Scope.DRIVE_FILE,
)


def _granted(provider: CredentialProvider) -> ScopeSet:
    return ScopeSet(provider.scopes())


def _has_any(granted: ScopeSet, candidates: ScopeSet) -> bool:
    return bool(granted.values & candidates.values)


def require_drive_extra() -> None:
    """Ensure the ``gdrive`` extra is installed.

    Raises:
        MissingExtraError: When Drive client libraries are missing.
    """
    require_extra("gdrive")


def require_drive_export_scopes(provider: CredentialProvider) -> None:
    """Require a Drive scope suitable for export.

    Raises:
        InsufficientScopesError: When no Drive read/export scope is present.
    """
    granted = _granted(provider)
    if _has_any(granted, _EXPORT_SCOPES):
        return
    raise InsufficientScopesError(
        "Exporting Docs/Slides files requires a Google Drive scope. "
        "Reauthorize including Drive (for example drive.readonly or drive.file). "
        "GoogleKit does not silently add Drive scopes.",
        required_scopes=_EXPORT_SCOPES.as_list(),
        granted_scopes=granted.as_list(),
    )


def require_drive_share_scopes(provider: CredentialProvider) -> None:
    """Require a Drive scope suitable for sharing.

    Raises:
        InsufficientScopesError: When no Drive write/share scope is present.
    """
    granted = _granted(provider)
    if _has_any(granted, _SHARE_SCOPES):
        return
    raise InsufficientScopesError(
        "Sharing Docs/Slides files requires a Google Drive write scope "
        "(drive or drive.file). GoogleKit does not silently add Drive scopes.",
        required_scopes=_SHARE_SCOPES.as_list(),
        granted_scopes=granted.as_list(),
    )


def drive_transport(
    provider: CredentialProvider,
    config: ClientConfig | None = None,
) -> Transport:
    """Build a Drive Transport after verifying the ``gdrive`` extra."""
    require_drive_extra()
    return Transport(provider, config or ClientConfig(), extra="gdrive")


def export_via_drive(
    provider: CredentialProvider,
    file_id: str,
    export_format: str,
    destination: str | Path | None = None,
    *,
    config: ClientConfig | None = None,
    source_mime: str,
) -> Any:
    """Export a Google-native file through Drive.

    Prefers ``FilesManager.export`` when available; otherwise uses
    ``DriveTransfers`` with resolved MIME types.

    Args:
        provider: Shared credential provider.
        file_id: Drive file / Docs / Slides ID.
        export_format: Short name (``pdf``, ``docx``, …) or full MIME type.
        destination: Optional local path; when omitted, bytes are returned.
        config: Optional client config.
        source_mime: Source Google-native MIME type.

    Returns:
        A ``DownloadResult`` from googlekit.gdrive.
    """
    require_drive_extra()
    require_drive_export_scopes(provider)
    fid = require_non_empty(file_id, "file_id")
    require_non_empty(export_format, "export_format")

    transport = drive_transport(provider, config)

    try:
        from googlekit.gdrive.files import FilesManager

        return FilesManager(transport).export(
            fid,
            export_format,
            destination,
        )
    except ImportError:
        pass

    from googlekit.gdrive.transfers import DriveTransfers, resolve_export_mime

    mime = resolve_export_mime(source_mime, export_format)
    transfers = DriveTransfers(transport)
    if destination is None:
        return transfers.download_bytes(fid, export_mime=mime)
    return transfers.download_path(fid, destination, export_mime=mime)


def share_via_drive(
    provider: CredentialProvider,
    file_id: str,
    *,
    email: str | None = None,
    role: str = "reader",
    type: str = "user",
    domain: str | None = None,
    send_notification: bool = False,
    config: ClientConfig | None = None,
) -> Any:
    """Create a Drive permission on a Docs/Slides file.

    Prefers ``PermissionsManager`` when available; otherwise calls
    ``permissions.create`` directly.

    Args:
        provider: Shared credential provider.
        file_id: Drive file ID (same as document/presentation ID).
        email: Email for ``user`` / ``group`` types.
        role: ``reader``, ``commenter``, or ``writer``.
        type: ``user``, ``group``, ``domain``, or ``anyone``.
        domain: Required when ``type`` is ``domain``.
        send_notification: Whether to email the recipient.
        config: Optional client config.

    Returns:
        A ``Permission`` model or raw API dict.
    """
    require_drive_extra()
    require_drive_share_scopes(provider)
    fid = require_non_empty(file_id, "file_id")
    role = require_non_empty(role, "role")
    perm_type = require_non_empty(type, "type")

    if perm_type in {"user", "group"} and not email:
        raise ValidationError(f"email is required when type={perm_type!r}")
    if perm_type == "domain" and not domain:
        raise ValidationError("domain is required when type='domain'")

    transport = drive_transport(provider, config)

    try:
        from googlekit.gdrive.permissions import PermissionsManager

        perms = PermissionsManager(transport)
        if hasattr(perms, "create"):
            return perms.create(
                fid,
                role=role,
                type=perm_type,
                email=email,
                domain=domain,
                send_notification=send_notification,
            )
        if perm_type == "user" and email and hasattr(perms, "share_with_user"):
            return perms.share_with_user(
                fid,
                email,
                role=role,
                send_notification=send_notification,
            )
    except ImportError:
        pass

    body: dict[str, Any] = {"type": perm_type, "role": role}
    if email:
        body["emailAddress"] = email
    if domain:
        body["domain"] = domain

    service = transport.get_service("drive", "v3")
    request = service.permissions().create(
        fileId=fid,
        body=body,
        sendNotificationEmail=send_notification,
        fields="id,type,role,emailAddress,displayName,domain,allowFileDiscovery",
        supportsAllDrives=transport.config.supports_all_drives,
    )
    data = transport.execute(request)

    try:
        from googlekit.gdrive.models import Permission

        return Permission.from_api(data)
    except ImportError:
        return data
