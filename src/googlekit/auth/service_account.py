"""Service account credential provider."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from googlekit.auth.scopes import ScopeSet
from googlekit.core.exceptions import AuthenticationError, ConfigurationError
from googlekit.core.optional import require_extra


class ServiceAccountCredentialProvider:
    """Authenticate with a service-account JSON key.

    Ordinary service accounts do not automatically access a personal user's Drive.
    Share files/folders with the service account email, or configure Workspace
    domain-wide delegation and pass ``subject``.
    """

    def __init__(
        self,
        credentials_file: str | Path,
        *,
        scopes: ScopeSet,
        subject: str | None = None,
        extra: str = "gdrive",
    ) -> None:
        self._path = Path(credentials_file)
        self._scopes = scopes
        self._subject = subject
        self._extra = extra
        self._credentials: Any | None = None

    def scopes(self) -> frozenset[str]:
        return self._scopes.values

    def credentials(self) -> Any:
        if self._credentials is not None:
            return self._credentials
        require_extra(self._extra)
        from google.oauth2 import service_account

        if not self._path.exists():
            raise ConfigurationError(f"Service account file not found: {self._path}")
        try:
            creds = service_account.Credentials.from_service_account_file(  # type: ignore[no-untyped-call]
                str(self._path),
                scopes=list(self._scopes.values),
            )
            if self._subject:
                # Domain-wide delegation requires Workspace admin configuration.
                creds = creds.with_subject(self._subject)
            self._credentials = creds
            return creds
        except Exception as exc:
            raise AuthenticationError(f"Service account authentication failed: {exc}") from exc
