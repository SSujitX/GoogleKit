"""OAuth credential provider tests (fully mocked)."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from googlekit.auth.oauth import OAuthCredentialProvider
from googlekit.auth.scopes import Scope, ScopeSet
from googlekit.auth.token_store import InMemoryTokenStore
from googlekit.core.exceptions import AuthenticationError, ConfigurationError


def _scopes() -> ScopeSet:
    return ScopeSet.of(Scope.DRIVE_FILE)


def test_oauth_missing_client_secrets_raises(tmp_path: Path) -> None:
    provider = OAuthCredentialProvider(
        tmp_path / "missing.json",
        scopes=_scopes(),
        token_store=InMemoryTokenStore(),
    )
    with patch("googlekit.auth.oauth.require_extra"):
        with pytest.raises(ConfigurationError, match="client secrets not found"):
            provider.credentials()


def test_oauth_uses_valid_cached_token(client_secrets_file: Path) -> None:
    store = InMemoryTokenStore()
    store.save(json.dumps({"token": "cached", "scopes": ["https://www.googleapis.com/auth/drive.file"]}))
    provider = OAuthCredentialProvider(
        client_secrets_file,
        scopes=_scopes(),
        token_store=store,
    )
    creds = SimpleNamespace(
        valid=True,
        expired=False,
        refresh_token=None,
        scopes=["https://www.googleapis.com/auth/drive.file"],
    )

    with (
        patch("googlekit.auth.oauth.require_extra"),
        patch(
            "google.oauth2.credentials.Credentials.from_authorized_user_info",
            return_value=creds,
        ) as from_info,
    ):
        result = provider.credentials()

    assert result is creds
    # Must load without injecting newly requested scopes into from_authorized_user_info.
    assert from_info.call_args.args[0]  # info dict
    assert len(from_info.call_args.args) == 1 or from_info.call_args.kwargs.get("scopes") in (
        None,
        [],
    )
    assert provider.credentials() is creds


def test_oauth_reauths_when_cached_scopes_insufficient(client_secrets_file: Path) -> None:
    store = InMemoryTokenStore()
    store.save("{}")
    provider = OAuthCredentialProvider(
        client_secrets_file,
        scopes=ScopeSet.of(Scope.DRIVE_FILE, Scope.SPREADSHEETS),
        token_store=store,
    )
    narrow = SimpleNamespace(
        valid=True,
        expired=False,
        refresh_token=None,
        scopes=["https://www.googleapis.com/auth/drive.file"],
    )
    fresh = MagicMock()
    fresh.to_json.return_value = '{"access_token": "fresh"}'
    flow = MagicMock()
    flow.run_local_server.return_value = fresh

    with (
        patch("googlekit.auth.oauth.require_extra"),
        patch(
            "google.oauth2.credentials.Credentials.from_authorized_user_info",
            return_value=narrow,
        ),
        patch(
            "google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file",
            return_value=flow,
        ),
    ):
        result = provider.credentials()

    assert result is fresh
    flow.run_local_server.assert_called_once()


def test_oauth_uses_actual_granted_scopes_for_granular_consent(
    client_secrets_file: Path,
) -> None:
    provider = OAuthCredentialProvider(
        client_secrets_file,
        scopes=ScopeSet.of(Scope.DRIVE_FILE, Scope.SPREADSHEETS),
        token_store=InMemoryTokenStore(),
    )
    creds = SimpleNamespace(
        scopes=[str(Scope.DRIVE_FILE), str(Scope.SPREADSHEETS)],
        granted_scopes=[str(Scope.DRIVE_FILE)],
    )

    assert provider._token_covers_required(creds) is False


def test_oauth_full_scope_covers_narrow_requested_scope(client_secrets_file: Path) -> None:
    provider = OAuthCredentialProvider(
        client_secrets_file,
        scopes=ScopeSet.of(Scope.DRIVE_FILE),
        token_store=InMemoryTokenStore(),
    )
    creds = SimpleNamespace(scopes=[str(Scope.DRIVE)], granted_scopes=None)

    assert provider._token_covers_required(creds) is True


def test_oauth_refresh_expired_token(client_secrets_file: Path) -> None:
    store = InMemoryTokenStore()
    store.save("{}")
    provider = OAuthCredentialProvider(
        client_secrets_file,
        scopes=_scopes(),
        token_store=store,
    )
    creds = MagicMock()
    creds.valid = False
    creds.expired = True
    creds.refresh_token = "refresh-token"
    creds.scopes = ["https://www.googleapis.com/auth/drive.file"]
    creds.to_json.return_value = '{"access_token": "new"}'

    def _refresh(_request: object) -> None:
        creds.valid = True

    creds.refresh.side_effect = _refresh

    with (
        patch("googlekit.auth.oauth.require_extra"),
        patch(
            "google.oauth2.credentials.Credentials.from_authorized_user_info",
            return_value=creds,
        ),
        patch("google.auth.transport.requests.Request"),
    ):
        result = provider.credentials()

    assert result is creds
    creds.refresh.assert_called_once()
    assert store.load() == '{"access_token": "new"}'


def test_oauth_browser_flow_when_no_token(client_secrets_file: Path) -> None:
    store = InMemoryTokenStore()
    provider = OAuthCredentialProvider(
        client_secrets_file,
        scopes=_scopes(),
        token_store=store,
    )
    fresh = MagicMock()
    fresh.to_json.return_value = '{"access_token": "fresh"}'
    flow = MagicMock()
    flow.run_local_server.return_value = fresh

    with (
        patch("googlekit.auth.oauth.require_extra"),
        patch(
            "google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file",
            return_value=flow,
        ),
    ):
        result = provider.credentials()

    assert result is fresh
    flow.run_local_server.assert_called_once_with(port=0)
    assert store.load() == '{"access_token": "fresh"}'


def test_oauth_browser_cancel_raises_authentication_error(client_secrets_file: Path) -> None:
    provider = OAuthCredentialProvider(
        client_secrets_file,
        scopes=_scopes(),
        token_store=InMemoryTokenStore(),
    )
    with (
        patch("googlekit.auth.oauth.require_extra"),
        patch(
            "google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file",
            side_effect=RuntimeError("cancelled"),
        ),
        pytest.raises(AuthenticationError, match=r"cancelled|failed"),
    ):
        provider.credentials()


def test_oauth_scopes_property(client_secrets_file: Path) -> None:
    provider = OAuthCredentialProvider(
        client_secrets_file,
        scopes=_scopes(),
        token_store=InMemoryTokenStore(),
    )
    assert Scope.DRIVE_FILE in provider.scopes()


def test_oauth_refresh_failure_falls_back_to_browser(client_secrets_file: Path) -> None:
    store = InMemoryTokenStore()
    store.save("{}")
    provider = OAuthCredentialProvider(
        client_secrets_file,
        scopes=_scopes(),
        token_store=store,
    )
    expired = MagicMock()
    expired.valid = False
    expired.expired = True
    expired.refresh_token = "rt"
    expired.scopes = ["https://www.googleapis.com/auth/drive.file"]
    expired.refresh.side_effect = RuntimeError("network")

    fresh = MagicMock()
    fresh.to_json.return_value = '{"access_token": "browser"}'
    flow = MagicMock()
    flow.run_local_server.return_value = fresh

    with (
        patch("googlekit.auth.oauth.require_extra"),
        patch(
            "google.oauth2.credentials.Credentials.from_authorized_user_info",
            return_value=expired,
        ),
        patch("google.auth.transport.requests.Request"),
        patch(
            "google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file",
            return_value=flow,
        ),
    ):
        result = provider.credentials()

    assert result is fresh
