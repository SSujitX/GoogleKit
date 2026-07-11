"""Unified GoogleKit client construction."""

from __future__ import annotations

import pytest

from googlekit.client import GoogleKit, _resolve_scopes
from googlekit.core.exceptions import ConfigurationError
from googlekit.auth.scopes import ScopeProfile, ScopeSet, Scope


def test_resolve_scopes_requires_services_or_scopes() -> None:
    with pytest.raises(ConfigurationError, match="services="):
        _resolve_scopes(None, None, ScopeProfile.READWRITE)


def test_resolve_scopes_from_services() -> None:
    scopes = _resolve_scopes(None, ["gdrive"], ScopeProfile.READWRITE)
    assert Scope.DRIVE_FILE in scopes.values
    assert Scope.SPREADSHEETS not in scopes.values


def test_resolve_scopes_explicit_set() -> None:
    wanted = ScopeSet.of(Scope.DRIVE_FILE)
    assert _resolve_scopes(wanted, None, ScopeProfile.READWRITE) is wanted
