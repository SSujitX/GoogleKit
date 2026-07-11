"""Unit tests for Drive changes and folders managers."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from googlekit.gdrive.client import DriveClient


def _exec_result(payload: dict[str, Any]) -> MagicMock:
    req = MagicMock()
    req.execute.return_value = payload
    return req


def test_get_start_page_token(drive: DriveClient, mock_service: MagicMock) -> None:
    changes = mock_service.changes.return_value
    changes.getStartPageToken.return_value = _exec_result({"startPageToken": "1"})
    token = drive.changes.get_start_page_token()
    assert token == "1"
    kwargs = changes.getStartPageToken.call_args.kwargs
    assert kwargs["supportsAllDrives"] is True
    assert "includeItemsFromAllDrives" not in kwargs


def test_list_changes_uses_include_items(drive: DriveClient, mock_service: MagicMock) -> None:
    changes = mock_service.changes.return_value
    changes.list.return_value = _exec_result({"changes": [], "newStartPageToken": "2"})
    drive.changes.list("1")
    kwargs = changes.list.call_args.kwargs
    assert kwargs["includeItemsFromAllDrives"] is True
    assert kwargs["supportsAllDrives"] is True


def test_list_changes(drive: DriveClient, mock_service: MagicMock) -> None:
    changes = mock_service.changes.return_value
    changes.list.return_value = _exec_result(
        {
            "changes": [
                {
                    "changeType": "file",
                    "fileId": "f1",
                    "removed": False,
                    "file": {"id": "f1", "name": "a.txt"},
                }
            ],
            "newStartPageToken": "99",
        }
    )
    page = drive.changes.list("1")
    assert len(page.items) == 1
    assert page.items[0].file_id == "f1"
    assert page.items[0].file is not None
    assert page.next_page_token is None


def test_create_folder_and_path(drive: DriveClient, mock_service: MagicMock) -> None:
    files = mock_service.files.return_value
    # find existing for first segment → empty, then create; second segment same
    files.list.return_value = _exec_result({"files": []})
    files.create.side_effect = [
        _exec_result(
            {
                "id": "folder_a",
                "name": "Projects",
                "mimeType": "application/vnd.google-apps.folder",
            }
        ),
        _exec_result(
            {
                "id": "folder_b",
                "name": "2026",
                "mimeType": "application/vnd.google-apps.folder",
                "parents": ["folder_a"],
            }
        ),
    ]
    folder = drive.folders.create_path("Projects/2026")
    assert folder.id == "folder_b"
    assert files.create.call_count == 2
    first_body = files.create.call_args_list[0].kwargs["body"]
    assert first_body["mimeType"] == "application/vnd.google-apps.folder"
    # First find should scope to My Drive root, not the entire Drive.
    first_list_q = files.list.call_args_list[0].kwargs["q"]
    assert "'root' in parents" in first_list_q
