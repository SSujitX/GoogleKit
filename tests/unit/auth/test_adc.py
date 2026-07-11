"""ADC credential provider tests (mocked)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from googlekit.auth.adc import ADCCredentialProvider
from googlekit.auth.scopes import Scope, ScopeSet
from googlekit.core.exceptions import AuthenticationError


def _scopes() -> ScopeSet:
    return ScopeSet.of(Scope.CALENDAR_EVENTS)


def test_adc_success() -> None:
    provider = ADCCredentialProvider(scopes=_scopes())
    creds = MagicMock()
    with (
        patch("googlekit.auth.adc.require_extra"),
        patch("google.auth.default", return_value=(creds, "project-1")) as default,
    ):
        result = provider.credentials()

    assert result is creds
    default.assert_called_once()
    assert provider.credentials() is creds


def test_adc_quota_project() -> None:
    provider = ADCCredentialProvider(scopes=_scopes(), quota_project_id="quota-proj")
    base = MagicMock()
    with_quota = MagicMock()
    base.with_quota_project.return_value = with_quota

    with (
        patch("googlekit.auth.adc.require_extra"),
        patch("google.auth.default", return_value=(base, None)),
    ):
        result = provider.credentials()

    base.with_quota_project.assert_called_once_with("quota-proj")
    assert result is with_quota


def test_adc_unavailable() -> None:
    provider = ADCCredentialProvider(scopes=_scopes())
    with (
        patch("googlekit.auth.adc.require_extra"),
        patch("google.auth.default", side_effect=Exception("no adc")),
    ):
        with pytest.raises(AuthenticationError, match="Application Default Credentials"):
            provider.credentials()


def test_adc_scopes() -> None:
    provider = ADCCredentialProvider(scopes=_scopes())
    assert Scope.CALENDAR_EVENTS in provider.scopes()
