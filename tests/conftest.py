"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from googlekit.auth.scopes import Scope, ScopeSet
from googlekit.auth.token_store import InMemoryTokenStore


@pytest.fixture
def tmp_path_factory_dir(tmp_path: Path) -> Path:
    """Alias-friendly temp directory for credential fixtures."""
    return tmp_path


@pytest.fixture
def drive_file_scopes() -> ScopeSet:
    return ScopeSet.of(Scope.DRIVE_FILE)


@pytest.fixture
def memory_token_store() -> InMemoryTokenStore:
    return InMemoryTokenStore()


@pytest.fixture
def client_secrets_file(tmp_path: Path) -> Path:
    """Minimal OAuth installed-app client secrets JSON (not a real secret)."""
    path = tmp_path / "client_secret.json"
    path.write_text(
        """
        {
          "installed": {
            "client_id": "test-client-id.apps.googleusercontent.com",
            "project_id": "test-project",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_secret": "test-client-secret"
          }
        }
        """.strip(),
        encoding="utf-8",
    )
    return path


@pytest.fixture
def service_account_file(tmp_path: Path) -> Path:
    """Placeholder service-account JSON path (contents unused when mocked)."""
    path = tmp_path / "service-account.json"
    path.write_text("{}", encoding="utf-8")
    return path
