"""Unit tests for DriveClient constructors."""

from __future__ import annotations

from unittest.mock import MagicMock

from googlekit.core.configuration import ClientConfig
from googlekit.gdrive import DriveClient, DriveFile, OverwritePolicy
from googlekit.gdrive.client import DriveClient as DriveClientDirect


class FakeProvider:
    def credentials(self):
        return object()

    def scopes(self):
        return frozenset(["https://www.googleapis.com/auth/drive.file"])


def test_from_provider_and_managers() -> None:
    client = DriveClient.from_provider(FakeProvider(), config=ClientConfig())
    assert client.files is client.files
    assert client.folders is client.folders
    assert client.permissions is client.permissions
    assert client.changes is client.changes
    assert client.config.supports_all_drives is True


def test_public_exports() -> None:
    assert DriveClient is DriveClientDirect
    assert DriveFile is not None
    assert OverwritePolicy.OVERWRITE.value == "overwrite"


def test_supports_all_drives_false(monkeypatch) -> None:
    client = DriveClient(
        FakeProvider(),
        config=ClientConfig(supports_all_drives=False),
    )
    service = MagicMock()
    monkeypatch.setattr(client.transport, "get_service", lambda a, v: service)
    req = MagicMock()
    req.execute.return_value = {"id": "f", "name": "n"}
    service.files.return_value.get.return_value = req
    client.files.get("f")
    assert "supportsAllDrives" not in service.files.return_value.get.call_args.kwargs
