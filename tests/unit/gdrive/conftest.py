"""Shared fixtures for Google Drive unit tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from googlekit.core.configuration import ClientConfig
from googlekit.core.retries import RetryPolicy
from googlekit.core.transport import Transport
from googlekit.gdrive.client import DriveClient


class FakeProvider:
    """Minimal CredentialProvider for unit tests."""

    def credentials(self) -> Any:
        return object()

    def scopes(self) -> frozenset[str]:
        return frozenset(["https://www.googleapis.com/auth/drive"])


@pytest.fixture
def provider() -> FakeProvider:
    return FakeProvider()


@pytest.fixture
def config() -> ClientConfig:
    return ClientConfig(
        supports_all_drives=True,
        retry=RetryPolicy(enabled=False, max_attempts=1),
    )


@pytest.fixture
def mock_service() -> MagicMock:
    service = MagicMock(name="drive_service")
    service.files.return_value = MagicMock(name="files_resource")
    service.permissions.return_value = MagicMock(name="permissions_resource")
    service.changes.return_value = MagicMock(name="changes_resource")
    return service


@pytest.fixture
def transport(
    provider: FakeProvider,
    config: ClientConfig,
    mock_service: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> Transport:
    transport = Transport(provider, config, extra="gdrive")
    monkeypatch.setattr(transport, "get_service", lambda api, ver: mock_service)
    return transport


@pytest.fixture
def drive(
    provider: FakeProvider,
    config: ClientConfig,
    mock_service: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> DriveClient:
    client = DriveClient(provider, config=config)
    monkeypatch.setattr(client.transport, "get_service", lambda api, ver: mock_service)
    return client
