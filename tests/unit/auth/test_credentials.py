"""Credential helper tests (mocked)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from googlekit.auth.credentials import auto_detect_credentials_file, build_provider
from googlekit.auth.scopes import Scope, ScopeSet
from googlekit.core.exceptions import AuthenticationError, ConfigurationError


def test_auto_detect_service_account(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "service_account.json").write_text("{}", encoding="utf-8")
    path, is_sa = auto_detect_credentials_file()
    assert path is not None
    assert path.name == "service_account.json"
    assert is_sa is True


def test_auto_detect_oauth(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "client_secrets.json").write_text("{}", encoding="utf-8")
    path, is_sa = auto_detect_credentials_file()
    assert path is not None
    assert is_sa is False


def test_build_provider_oauth_requires_secrets() -> None:
    with pytest.raises(ConfigurationError):
        build_provider(method="oauth", scopes=ScopeSet.of(Scope.DRIVE_FILE))


def test_build_provider_adc(monkeypatch: pytest.MonkeyPatch) -> None:
    scopes = ScopeSet.of(Scope.DRIVE_FILE)
    with patch("googlekit.auth.adc.require_extra"), patch("google.auth.default") as default:
        default.return_value = (MagicMock(valid=True), "proj")
        provider = build_provider(method="adc", scopes=scopes)
        creds = provider.credentials()
        assert creds is not None


def test_build_provider_auto_fails_cleanly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    scopes = ScopeSet.of(Scope.DRIVE_FILE)
    with patch("googlekit.auth.adc.require_extra"):
        with patch("google.auth.default", side_effect=Exception("no adc")):
            with pytest.raises(AuthenticationError):
                build_provider(method="auto", scopes=scopes)
