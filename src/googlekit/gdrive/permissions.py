"""Google Drive permissions / sharing manager."""

from __future__ import annotations

import logging
from typing import Any

from googlekit.core.exceptions import ValidationError
from googlekit.core.transport import Transport
from googlekit.core.validation import require_non_empty
from googlekit.gdrive.models import (
    PERMISSION_FIELDS,
    Permission,
    PermissionRole,
    shared_drive_params,
)

logger = logging.getLogger(__name__)

_VALID_ROLES = {r.value for r in PermissionRole}


class PermissionsManager:
    """List and mutate Drive sharing permissions."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def _service(self) -> Any:
        return self._transport.get_service("drive", "v3")

    @property
    def _sd(self) -> dict[str, bool]:
        return shared_drive_params(self._transport.config.supports_all_drives)

    def list(
        self,
        file_id: str,
        *,
        fields: str = PERMISSION_FIELDS,
    ) -> list[Permission]:
        """List permissions on a file or folder."""
        require_non_empty(file_id, "file_id")
        response = self._transport.execute(
            self._service()
            .permissions()
            .list(
                fileId=file_id,
                fields=f"permissions({fields})",
                **self._sd,
            )
        )
        return [Permission.from_api(p) for p in response.get("permissions", [])]

    def share_user(
        self,
        file_id: str,
        email: str,
        *,
        role: PermissionRole | str = PermissionRole.READER,
        notify: bool = True,
        message: str | None = None,
    ) -> Permission:
        """Share with a Google account email."""
        require_non_empty(email, "email")
        return self._create_permission(
            file_id,
            body={
                "type": "user",
                "role": self._role(role),
                "emailAddress": email,
            },
            send_notification=notify,
            email_message=message,
        )

    def share_group(
        self,
        file_id: str,
        email: str,
        *,
        role: PermissionRole | str = PermissionRole.READER,
        notify: bool = True,
        message: str | None = None,
    ) -> Permission:
        """Share with a Google Group email."""
        require_non_empty(email, "email")
        return self._create_permission(
            file_id,
            body={
                "type": "group",
                "role": self._role(role),
                "emailAddress": email,
            },
            send_notification=notify,
            email_message=message,
        )

    def share_anyone(
        self,
        file_id: str,
        *,
        role: PermissionRole | str = PermissionRole.READER,
        allow_file_discovery: bool = False,
        public: bool = False,
    ) -> Permission:
        """Create an ``anyone`` permission.

        Public link sharing is only performed when ``public=True`` is passed
        explicitly (safety guard against accidental exposure).
        """
        if not public:
            raise ValidationError(
                "share_anyone requires public=True to create a public link. "
                "This guard prevents accidental public sharing."
            )
        body: dict[str, Any] = {
            "type": "anyone",
            "role": self._role(role),
            "allowFileDiscovery": allow_file_discovery,
        }
        return self._create_permission(file_id, body=body, send_notification=False)

    def change_role(
        self,
        file_id: str,
        permission_id: str,
        role: PermissionRole | str,
    ) -> Permission:
        """Update the role on an existing permission."""
        require_non_empty(file_id, "file_id")
        require_non_empty(permission_id, "permission_id")
        response = self._transport.execute(
            self._service()
            .permissions()
            .update(
                fileId=file_id,
                permissionId=permission_id,
                body={"role": self._role(role)},
                fields=PERMISSION_FIELDS,
                **self._sd,
            )
        )
        return Permission.from_api(response)

    def remove(self, file_id: str, permission_id: str) -> None:
        """Delete a permission by id."""
        require_non_empty(file_id, "file_id")
        require_non_empty(permission_id, "permission_id")
        self._transport.execute(
            self._service()
            .permissions()
            .delete(
                fileId=file_id,
                permissionId=permission_id,
                **self._sd,
            )
        )

    def create_shareable_link(
        self,
        file_id: str,
        *,
        role: PermissionRole | str = PermissionRole.READER,
        public: bool = False,
    ) -> str:
        """Ensure link sharing and return ``webViewLink``.

        Requires ``public=True`` so public sharing is never implicit.
        """
        if not public:
            raise ValidationError(
                "create_shareable_link requires public=True. "
                "Pass public=True only when you intentionally want anyone-with-link access."
            )
        existing = [
            p for p in self.list(file_id) if p.type == "anyone" and p.role == self._role(role)
        ]
        if not existing:
            self.share_anyone(file_id, role=role, public=True)
        meta = self._transport.execute(
            self._service()
            .files()
            .get(
                fileId=file_id,
                fields="webViewLink",
                **self._sd,
            )
        )
        link = meta.get("webViewLink")
        if not link:
            raise ValidationError(f"No webViewLink available for file {file_id!r}")
        return str(link)

    def _create_permission(
        self,
        file_id: str,
        *,
        body: dict[str, Any],
        send_notification: bool,
        email_message: str | None = None,
    ) -> Permission:
        require_non_empty(file_id, "file_id")
        kwargs: dict[str, Any] = {
            "fileId": file_id,
            "body": body,
            "fields": PERMISSION_FIELDS,
            "sendNotificationEmail": send_notification,
            **self._sd,
        }
        if email_message and send_notification:
            kwargs["emailMessage"] = email_message
        response = self._transport.execute(self._service().permissions().create(**kwargs))
        logger.debug(
            "Created permission %s on %s (type=%s role=%s)",
            response.get("id"),
            file_id,
            body.get("type"),
            body.get("role"),
        )
        return Permission.from_api(response)

    @staticmethod
    def _role(role: PermissionRole | str) -> str:
        value = str(role)
        if value not in _VALID_ROLES:
            raise ValidationError(
                f"Invalid permission role {value!r}. Valid roles: {', '.join(sorted(_VALID_ROLES))}"
            )
        return value
