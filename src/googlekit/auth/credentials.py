"""Credential helpers and auto-detection (inspired by PyDrive4 patterns)."""

from __future__ import annotations

from glob import glob
from pathlib import Path

from googlekit.auth.adc import ADCCredentialProvider
from googlekit.auth.oauth import OAuthCredentialProvider
from googlekit.auth.scopes import ScopeProfile, ScopeSet, aggregate_scopes, preset_for
from googlekit.auth.service_account import ServiceAccountCredentialProvider
from googlekit.auth.token_store import FileTokenStore
from googlekit.core.exceptions import AuthenticationError, ConfigurationError
from googlekit.core.protocols import CredentialProvider

AUTO_DETECT_SERVICE_ACCOUNT_FILES = (
    "service_account.json",
    "service_account_key.json",
    "sa_credentials.json",
)

AUTO_DETECT_OAUTH_FILES = (
    "client_secrets.json",
    "client_secret.json",
    "credentials.json",
    "oauth_credentials.json",
)


def auto_detect_credentials_file(cwd: Path | None = None) -> tuple[Path | None, bool]:
    """Detect a credentials JSON in ``cwd``.

    Returns:
        (path, is_service_account)
    """
    root = cwd or Path.cwd()
    for name in AUTO_DETECT_SERVICE_ACCOUNT_FILES:
        path = root / name
        if path.exists():
            return path, True
    for name in AUTO_DETECT_OAUTH_FILES:
        path = root / name
        if path.exists():
            return path, False
    matches = sorted(glob(str(root / "client_secret_*.json")))
    if matches:
        return Path(matches[0]), False
    return None, False


def build_provider(
    *,
    method: str = "auto",
    client_secrets: str | Path | None = None,
    service_account_file: str | Path | None = None,
    token_path: str | Path | None = None,
    subject: str | None = None,
    quota_project_id: str | None = None,
    scopes: ScopeSet | None = None,
    services: list[str] | None = None,
    profile: ScopeProfile = ScopeProfile.READWRITE,
    extra: str = "gdrive",
) -> CredentialProvider:
    """Build a credential provider from explicit args or auto-detection."""
    scope_set = scopes
    if scope_set is None:
        svc = services or ["gdrive"]
        scope_set = aggregate_scopes(*(preset_for(s, profile) for s in svc))

    method = method.lower()
    if method == "oauth":
        if not client_secrets:
            raise ConfigurationError("client_secrets is required for OAuth")
        return OAuthCredentialProvider(
            client_secrets,
            scopes=scope_set,
            token_path=token_path,
            extra=extra,
        )
    if method == "service_account":
        if not service_account_file:
            raise ConfigurationError("credentials_file is required for service accounts")
        return ServiceAccountCredentialProvider(
            service_account_file,
            scopes=scope_set,
            subject=subject,
            extra=extra,
        )
    if method == "adc":
        return ADCCredentialProvider(
            scopes=scope_set,
            quota_project_id=quota_project_id,
            extra=extra,
        )

    # auto: ADC → detected file → error
    try:
        adc = ADCCredentialProvider(
            scopes=scope_set, quota_project_id=quota_project_id, extra=extra
        )
        adc.credentials()
        return adc
    except Exception:
        pass

    path, is_sa = auto_detect_credentials_file()
    if path is None:
        raise AuthenticationError(
            "No credentials available. Options:\n"
            "  1. Run: gcloud auth application-default login\n"
            "  2. Place client_secrets.json or service_account.json in the working directory\n"
            "  3. Pass credentials explicitly to from_oauth / from_service_account / from_adc"
        )
    if is_sa:
        return ServiceAccountCredentialProvider(
            path, scopes=scope_set, subject=subject, extra=extra
        )
    store = FileTokenStore(token_path) if token_path else None
    return OAuthCredentialProvider(
        path,
        scopes=scope_set,
        token_store=store,
        token_path=token_path,
        extra=extra,
    )
