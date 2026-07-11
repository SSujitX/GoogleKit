"""Authentication package."""

from __future__ import annotations

from googlekit.auth.adc import ADCCredentialProvider
from googlekit.auth.credentials import auto_detect_credentials_file, build_provider
from googlekit.auth.oauth import OAuthCredentialProvider
from googlekit.auth.scopes import (
    CALENDAR_PRESETS,
    DOCS_PRESETS,
    DRIVE_PRESETS,
    SHEETS_PRESETS,
    SLIDES_PRESETS,
    Scope,
    ScopeProfile,
    ScopeSet,
    aggregate_scopes,
    preset_for,
)
from googlekit.auth.service_account import ServiceAccountCredentialProvider
from googlekit.auth.token_store import FileTokenStore, InMemoryTokenStore, default_token_path

__all__ = [
    "CALENDAR_PRESETS",
    "DOCS_PRESETS",
    "DRIVE_PRESETS",
    "SHEETS_PRESETS",
    "SLIDES_PRESETS",
    "ADCCredentialProvider",
    "FileTokenStore",
    "InMemoryTokenStore",
    "OAuthCredentialProvider",
    "Scope",
    "ScopeProfile",
    "ScopeSet",
    "ServiceAccountCredentialProvider",
    "aggregate_scopes",
    "auto_detect_credentials_file",
    "build_provider",
    "default_token_path",
    "preset_for",
]
