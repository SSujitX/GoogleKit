"""Auto-detect credentials and build_provider tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from googlekit.auth.adc import ADCCredentialProvider
from googlekit.auth.credentials import auto_detect_credentials_file, build_provider
from googlekit.auth.oauth import OAuthCredentialProvider
from googlekit.auth.scopes import Scope, ScopeSet
from googlekit.auth.service_account import ServiceAccountCredentialProvider
from googlekit.core.exceptions import AuthenticationError, ConfigurationError


def _scopes() -> ScopeSet:
    return ScopeSet.of(Scope.DRIVE_FILE)


def test_auto_detect_service_account(tmp_path: Path) -> None:
    path = tmp_path / "service_account.json"
    path.write_text("{}", encoding="utf-8")
    found, is_sa = auto_detect_credentials_file(tmp_path)
    assert found == path
    assert is_sa is True


def test_auto_detect_oauth_client_secrets(tmp_path: Path) -> None:
    path = tmp_path / "client_secrets.json"
    path.write_text("{}", encoding="utf-8")
    found, is_sa = auto_detect_credentials_file(tmp_path)
    assert found == path
    assert is_sa is False


def test_auto_detect_client_secret_glob(tmp_path: Path) -> None:
    path = tmp_path / "client_secret_1234.json"
    path.write_text("{}", encoding="utf-8")
    found, is_sa = auto_detect_credentials_file(tmp_path)
    assert found == path
    assert is_sa is False


def test_auto_detect_none(tmp_path: Path) -> None:
    found, is_sa = auto_detect_credentials_file(tmp_path)
    assert found is None
    assert is_sa is False


def test_build_provider_oauth_requires_secrets() -> None:
    with pytest.raises(ConfigurationError, match="client_secrets"):
        build_provider(method="oauth", scopes=_scopes())


def test_build_provider_oauth(client_secrets_file: Path) -> None:
    provider = build_provider(
        method="oauth",
        client_secrets=client_secrets_file,
        scopes=_scopes(),
    )
    assert isinstance(provider, OAuthCredentialProvider)


def test_build_provider_service_account_requires_file() -> None:
    with pytest.raises(ConfigurationError, match="credentials_file"):
        build_provider(method="service_account", scopes=_scopes())


def test_build_provider_service_account(service_account_file: Path) -> None:
    provider = build_provider(
        method="service_account",
        service_account_file=service_account_file,
        scopes=_scopes(),
    )
    assert isinstance(provider, ServiceAccountCredentialProvider)


def test_build_provider_adc() -> None:
    provider = build_provider(method="adc", scopes=_scopes())
    assert isinstance(provider, ADCCredentialProvider)


def test_build_provider_auto_prefers_adc() -> None:
    adc = MagicMock(spec=ADCCredentialProvider)
    adc.credentials.return_value = MagicMock()
    with patch(
        "googlekit.auth.credentials.ADCCredentialProvider",
        return_value=adc,
    ):
        provider = build_provider(method="auto", scopes=_scopes())
    assert provider is adc


def test_build_provider_auto_falls_back_to_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sa = tmp_path / "service_account.json"
    sa.write_text("{}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    with patch("googlekit.auth.credentials.ADCCredentialProvider") as adc_cls:
        instance = MagicMock()
        instance.credentials.side_effect = Exception("no adc")
        adc_cls.return_value = instance
        provider = build_provider(method="auto", scopes=_scopes())

    assert isinstance(provider, ServiceAccountCredentialProvider)


def test_build_provider_auto_no_credentials(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    with patch("googlekit.auth.credentials.ADCCredentialProvider") as adc_cls:
        instance = MagicMock()
        instance.credentials.side_effect = Exception("no adc")
        adc_cls.return_value = instance
        with pytest.raises(AuthenticationError, match="No credentials available"):
            build_provider(method="auto", scopes=_scopes())
