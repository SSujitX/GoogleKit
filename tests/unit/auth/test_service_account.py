"""Service account provider tests (mocked construction)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from googlekit.auth.scopes import Scope, ScopeSet
from googlekit.auth.service_account import ServiceAccountCredentialProvider
from googlekit.core.exceptions import AuthenticationError, ConfigurationError


def _scopes() -> ScopeSet:
    return ScopeSet.of(Scope.SPREADSHEETS)


def test_service_account_missing_file(tmp_path: Path) -> None:
    provider = ServiceAccountCredentialProvider(
        tmp_path / "missing.json",
        scopes=_scopes(),
    )
    with patch("googlekit.auth.service_account.require_extra"):
        with pytest.raises(ConfigurationError, match="not found"):
            provider.credentials()


def test_service_account_construction(service_account_file: Path) -> None:
    provider = ServiceAccountCredentialProvider(
        service_account_file,
        scopes=_scopes(),
    )
    creds = MagicMock()
    with (
        patch("googlekit.auth.service_account.require_extra"),
        patch(
            "google.oauth2.service_account.Credentials.from_service_account_file",
            return_value=creds,
        ) as factory,
    ):
        result = provider.credentials()

    assert result is creds
    factory.assert_called_once()
    kwargs = factory.call_args.kwargs
    assert Scope.SPREADSHEETS in kwargs["scopes"]
    # Cached on second call
    assert provider.credentials() is creds


def test_service_account_with_subject(service_account_file: Path) -> None:
    provider = ServiceAccountCredentialProvider(
        service_account_file,
        scopes=_scopes(),
        subject="user@example.com",
    )
    base = MagicMock()
    delegated = MagicMock()
    base.with_subject.return_value = delegated

    with (
        patch("googlekit.auth.service_account.require_extra"),
        patch(
            "google.oauth2.service_account.Credentials.from_service_account_file",
            return_value=base,
        ),
    ):
        result = provider.credentials()

    base.with_subject.assert_called_once_with("user@example.com")
    assert result is delegated


def test_service_account_failure_wraps(service_account_file: Path) -> None:
    provider = ServiceAccountCredentialProvider(
        service_account_file,
        scopes=_scopes(),
    )
    with (
        patch("googlekit.auth.service_account.require_extra"),
        patch(
            "google.oauth2.service_account.Credentials.from_service_account_file",
            side_effect=ValueError("bad key"),
        ),
        pytest.raises(AuthenticationError, match="Service account"),
    ):
        provider.credentials()


def test_service_account_scopes() -> None:
    provider = ServiceAccountCredentialProvider(
        "x.json",
        scopes=_scopes(),
    )
    assert provider.scopes() == frozenset({Scope.SPREADSHEETS})
