"""Unit tests for Drive permissions manager."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from googlekit.core.exceptions import ValidationError
from googlekit.gdrive.client import DriveClient
from googlekit.gdrive.models import PermissionRole


def _exec_result(payload: dict[str, Any]) -> MagicMock:
    req = MagicMock()
    req.execute.return_value = payload
    return req


def test_share_user(drive: DriveClient, mock_service: MagicMock) -> None:
    perms = mock_service.permissions.return_value
    perms.create.return_value = _exec_result(
        {
            "id": "perm_1",
            "type": "user",
            "role": "writer",
            "emailAddress": "alice@example.com",
        }
    )
    perm = drive.permissions.share_user(
        "file_1",
        "alice@example.com",
        role=PermissionRole.WRITER,
        notify=False,
    )
    assert perm.email_address == "alice@example.com"
    assert perm.role == "writer"
    kwargs = perms.create.call_args.kwargs
    assert kwargs["body"]["type"] == "user"
    assert kwargs["sendNotificationEmail"] is False
    assert kwargs["supportsAllDrives"] is True


def test_share_anyone_requires_explicit_public(
    drive: DriveClient,
    mock_service: MagicMock,
) -> None:
    with pytest.raises(ValidationError, match="public=True"):
        drive.permissions.share_anyone("file_1")
    mock_service.permissions.return_value.create.assert_not_called()


def test_share_anyone_when_explicit(
    drive: DriveClient,
    mock_service: MagicMock,
) -> None:
    perms = mock_service.permissions.return_value
    perms.create.return_value = _exec_result({"id": "anyone", "type": "anyone", "role": "reader"})
    perm = drive.permissions.share_anyone("file_1", public=True)
    assert perm.type == "anyone"
    assert perms.create.call_args.kwargs["body"]["type"] == "anyone"


def test_change_role_and_remove(drive: DriveClient, mock_service: MagicMock) -> None:
    perms = mock_service.permissions.return_value
    perms.update.return_value = _exec_result({"id": "perm_1", "type": "user", "role": "commenter"})
    updated = drive.permissions.change_role("file_1", "perm_1", "commenter")
    assert updated.role == "commenter"

    perms.delete.return_value = _exec_result({})
    drive.permissions.remove("file_1", "perm_1")
    assert perms.delete.call_args.kwargs["permissionId"] == "perm_1"


def test_invalid_role(drive: DriveClient) -> None:
    with pytest.raises(ValidationError, match="Invalid permission role"):
        drive.permissions.share_user("file_1", "a@b.com", role="not-a-role")


def test_share_anyone_omits_notification_flag(
    drive: DriveClient,
    mock_service: MagicMock,
) -> None:
    perms = mock_service.permissions.return_value
    perms.create.return_value = _exec_result({"id": "anyone", "type": "anyone", "role": "reader"})
    drive.permissions.share_anyone("file_1", public=True)
    kwargs = perms.create.call_args.kwargs
    assert "sendNotificationEmail" not in kwargs


def test_share_domain(drive: DriveClient, mock_service: MagicMock) -> None:
    perms = mock_service.permissions.return_value
    perms.create.return_value = _exec_result(
        {"id": "dom", "type": "domain", "role": "reader", "domain": "example.com"}
    )
    perm = drive.permissions.share_domain("file_1", "example.com", allow_file_discovery=True)
    assert perm.type == "domain"
    body = perms.create.call_args.kwargs["body"]
    assert body["domain"] == "example.com"
    assert body["allowFileDiscovery"] is True
    assert "sendNotificationEmail" not in perms.create.call_args.kwargs


def test_create_shareable_link(drive: DriveClient, mock_service: MagicMock) -> None:
    perms = mock_service.permissions.return_value
    files = mock_service.files.return_value
    perms.list.return_value = _exec_result({"permissions": []})
    perms.create.return_value = _exec_result({"id": "anyone", "type": "anyone", "role": "reader"})
    files.get.return_value = _exec_result(
        {"webViewLink": "https://drive.google.com/file/d/file_1/view"}
    )
    link = drive.permissions.create_shareable_link("file_1", public=True)
    assert link.endswith("/view")
