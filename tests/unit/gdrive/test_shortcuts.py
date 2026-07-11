"""Unit tests for optional Drive/Sheets convenience shortcuts."""

from __future__ import annotations

from unittest.mock import MagicMock

from googlekit.core.configuration import ClientConfig
from googlekit.core.pagination import Page
from googlekit.core.service_apis import DriveAPI, SheetsAPI
from googlekit.gdrive import DriveClient, DriveFile, OverwritePolicy
from googlekit.gdrive.models import Permission, PermissionRole, UploadResult
from googlekit.gsheets.client import SheetsClient


class FakeProvider:
    def credentials(self):
        return object()

    def scopes(self):
        return frozenset(["https://www.googleapis.com/auth/drive.file"])


def test_drive_shortcuts_delegate_to_managers() -> None:
    client = DriveClient(FakeProvider(), config=ClientConfig())
    page = Page(items=[], next_page_token=None)
    files = MagicMock()
    folders = MagicMock()
    permissions = MagicMock()
    files.list.return_value = page
    files.search.return_value = page
    folder = MagicMock()
    folders.create.return_value = folder
    upload = UploadResult(
        file=DriveFile(id="f1", name="a.txt"),
        bytes_uploaded=1,
    )
    files.upload_path.return_value = upload
    files.trash.return_value = DriveFile(id="f1", name="a.txt", trashed=True)
    perm = Permission(id="p1", type="user", role="reader", email_address="a@b.com")
    permissions.share_user.return_value = perm
    permissions.list.return_value = [perm]
    permissions.create_shareable_link.return_value = "https://drive.google.com/file"

    client._files = files
    client._folders = folders
    client._permissions = permissions

    assert client.list_files(folder_id="root") is page
    files.list.assert_called()
    assert client.list_folders(folder_id="root") is page
    assert client.search_files("report") is page
    assert client.search_folders("Projects") is page
    assert client.create_folder("X") is folder
    assert client.upload_file("a.txt", folder_id="parent", overwrite=True) is upload
    files.upload_path.assert_called()
    kwargs = files.upload_path.call_args.kwargs
    assert kwargs["parents"] == ["parent"]
    assert kwargs["overwrite"] is OverwritePolicy.OVERWRITE
    assert client.delete_file("f1") is not None
    files.trash.assert_called_with("f1")
    assert client.share("f1", email="a@b.com") is perm
    assert client.list_permissions("f1") == [perm]
    assert client.get_share_link("f1") == "https://drive.google.com/file"
    permissions.create_shareable_link.assert_called_with(
        "f1", role=PermissionRole.READER, public=True
    )


def test_driveapi_protocol_has_shortcuts() -> None:
    assert hasattr(DriveAPI, "list_files")
    assert hasattr(DriveAPI, "upload_file")
    assert hasattr(DriveAPI, "share")
    assert hasattr(SheetsAPI, "write_values")
    assert hasattr(SheetsAPI, "read_values")


def test_sheets_shortcuts_delegate() -> None:
    client = SheetsClient(FakeProvider(), config=ClientConfig())
    client.spreadsheets = MagicMock()
    client.values = MagicMock()
    sheet = MagicMock()
    client.spreadsheets.create.return_value = sheet
    client.spreadsheets.get.return_value = sheet
    vr = MagicMock()
    client.values.read.return_value = vr
    client.values.write.return_value = MagicMock()
    client.values.append.return_value = MagicMock()

    assert client.create_spreadsheet("T") is sheet
    assert client.get_spreadsheet("sid") is sheet
    assert client.read_values("sid", "A1") is vr
    client.write_values("sid", "A1", [["a"]])
    client.append_values("sid", "A1", [["b"]])
    client.values.write.assert_called()
    client.values.append.assert_called()


def test_drive_runtime_checkable() -> None:
    client = DriveClient(FakeProvider(), config=ClientConfig())
    assert isinstance(client, DriveAPI)
