"""Unit tests for Drive files manager (mocked service boundary)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from googlekit.core.exceptions import ValidationError
from googlekit.gdrive.client import DriveClient
from googlekit.gdrive.models import DriveFile, OverwritePolicy
from googlekit.gdrive.transfers import resolve_export_mime


def _exec_result(payload: dict[str, Any]) -> MagicMock:
    req = MagicMock()
    req.execute.return_value = payload
    return req


def test_upload_path_builds_create_request(
    drive: DriveClient,
    mock_service: MagicMock,
    tmp_path: Path,
) -> None:
    local = tmp_path / "report.pdf"
    local.write_bytes(b"%PDF-1.4 fake")

    files_api = mock_service.files.return_value
    # find_by_name → list returns empty
    files_api.list.return_value = _exec_result({"files": []})

    created = {
        "id": "file_abc",
        "name": "report.pdf",
        "mimeType": "application/pdf",
        "size": "13",
    }

    with patch("googleapiclient.http.MediaFileUpload") as media_cls:
        media_cls.return_value = MagicMock(name="media")
        create_req = MagicMock()
        create_req.resumable = None
        create_req.execute.return_value = created
        files_api.create.return_value = create_req

        result = drive.files.upload_path(local, parents=["folder_1"])

    assert result is not None
    assert result.file.id == "file_abc"
    assert result.overwritten is False
    kwargs = files_api.create.call_args.kwargs
    assert kwargs["body"]["name"] == "report.pdf"
    assert kwargs["body"]["parents"] == ["folder_1"]
    assert kwargs["supportsAllDrives"] is True
    assert kwargs["media_body"] is media_cls.return_value
    media_cls.assert_called_once()
    assert (
        str(local) in media_cls.call_args.args
        or media_cls.call_args.kwargs.get("filename") == str(local)
        or media_cls.call_args[0][0] == str(local)
    )


def test_trash_updates_metadata(drive: DriveClient, mock_service: MagicMock) -> None:
    files_api = mock_service.files.return_value
    files_api.update.return_value = _exec_result(
        {"id": "file_1", "name": "a.txt", "trashed": True, "mimeType": "text/plain"}
    )
    trashed = drive.files.trash("file_1")
    assert trashed.trashed is True
    kwargs = files_api.update.call_args.kwargs
    assert kwargs["fileId"] == "file_1"
    assert kwargs["body"] == {"trashed": True}
    assert kwargs["supportsAllDrives"] is True


def test_restore_and_delete(drive: DriveClient, mock_service: MagicMock) -> None:
    files_api = mock_service.files.return_value
    files_api.update.return_value = _exec_result(
        {"id": "file_1", "name": "a.txt", "trashed": False}
    )
    restored = drive.files.restore("file_1")
    assert restored.trashed is False

    files_api.delete.return_value = _exec_result({})
    drive.files.delete("file_1")
    assert files_api.delete.call_args.kwargs["fileId"] == "file_1"
    assert files_api.delete.call_args.kwargs["supportsAllDrives"] is True


def test_pagination_is_lazy(drive: DriveClient, mock_service: MagicMock) -> None:
    files_api = mock_service.files.return_value
    page1 = {
        "files": [{"id": "1", "name": "a"}, {"id": "2", "name": "b"}],
        "nextPageToken": "tok2",
    }
    page2 = {
        "files": [{"id": "3", "name": "c"}],
    }
    files_api.list.side_effect = [_exec_result(page1), _exec_result(page2)]

    iterator = drive.files.iterate(page_size=2)
    first = next(iterator)
    assert first.id == "1"
    assert files_api.list.call_count == 1  # second page not fetched yet

    remaining = list(iterator)
    assert [f.id for f in remaining] == ["2", "3"]
    assert files_api.list.call_count == 2


def test_export_format_error_lists_valid(drive: DriveClient, mock_service: MagicMock) -> None:
    files_api = mock_service.files.return_value
    files_api.get.return_value = _exec_result(
        {
            "id": "doc_1",
            "name": "Notes",
            "mimeType": "application/vnd.google-apps.document",
        }
    )
    with pytest.raises(ValidationError) as exc:
        drive.files.export("doc_1", "exe")
    message = str(exc.value)
    assert "Invalid export format" in message
    assert "pdf" in message
    assert "docx" in message


def test_resolve_export_mime_helpers() -> None:
    assert (
        resolve_export_mime("application/vnd.google-apps.spreadsheet", "xlsx")
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    # Official Drive export table: Docs/Sheets HTML is application/zip.
    assert (
        resolve_export_mime("application/vnd.google-apps.document", "html")
        == "application/zip"
    )
    assert (
        resolve_export_mime("application/vnd.google-apps.document", "markdown")
        == "text/markdown"
    )
    assert (
        resolve_export_mime("application/vnd.google-apps.presentation", "svg")
        == "image/svg+xml"
    )
    with pytest.raises(ValidationError):
        resolve_export_mime("application/pdf", "docx")
    with pytest.raises(ValidationError, match="files.download"):
        resolve_export_mime("application/vnd.google-apps.vid", "mp4")


def test_download_google_native_requires_export(
    drive: DriveClient,
    mock_service: MagicMock,
) -> None:
    files_api = mock_service.files.return_value
    files_api.get.return_value = _exec_result(
        {
            "id": "sheet_1",
            "name": "Budget",
            "mimeType": "application/vnd.google-apps.spreadsheet",
        }
    )
    with pytest.raises(ValidationError, match="Google-native"):
        drive.files.download_bytes("sheet_1")


def test_overwrite_skip(drive: DriveClient, mock_service: MagicMock, tmp_path: Path) -> None:
    local = tmp_path / "dup.txt"
    local.write_text("hello", encoding="utf-8")
    files_api = mock_service.files.return_value
    files_api.list.return_value = _exec_result(
        {"files": [{"id": "existing", "name": "dup.txt", "mimeType": "text/plain"}]}
    )
    result = drive.files.upload_path(
        local,
        parents=["root"],
        overwrite=OverwritePolicy.SKIP,
    )
    assert result is None
    files_api.create.assert_not_called()


def test_drive_file_model() -> None:
    f = DriveFile.from_api(
        {
            "id": "x",
            "name": "Folder",
            "mimeType": "application/vnd.google-apps.folder",
            "size": "10",
            "parents": ["root"],
        }
    )
    assert f.is_folder is True
    assert f.size == 10
    assert f.raw["id"] == "x"
