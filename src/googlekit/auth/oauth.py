"""OAuth 2.0 desktop credential provider."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from googlekit.auth.scopes import ScopeSet
from googlekit.auth.token_store import FileTokenStore, default_token_path
from googlekit.core.exceptions import AuthenticationError, ConfigurationError
from googlekit.core.optional import require_extra
from googlekit.core.protocols import TokenStore

logger = logging.getLogger(__name__)


class OAuthCredentialProvider:
    """Browser-based installed-app OAuth with token caching and refresh."""

    def __init__(
        self,
        client_secrets: str | Path,
        *,
        scopes: ScopeSet,
        token_store: TokenStore | None = None,
        token_path: str | Path | None = None,
        extra: str = "gdrive",
    ) -> None:
        self._client_secrets = Path(client_secrets)
        self._scopes = scopes
        self._extra = extra
        if token_store is not None:
            self._store = token_store
        elif token_path is not None:
            self._store = FileTokenStore(token_path)
        else:
            self._store = FileTokenStore(default_token_path())
        self._credentials: Any | None = None

    def scopes(self) -> frozenset[str]:
        return self._scopes.values

    def credentials(self) -> Any:
        if self._credentials is not None and self._credentials.valid:
            if self._token_covers_required(self._credentials):
                return self._credentials
            # In-memory creds no longer cover required scopes (caller expanded).
            self._credentials = None
        self._credentials = self._authenticate()
        return self._credentials

    def _authenticate(self) -> Any:
        require_extra(self._extra)
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow

        if not self._client_secrets.exists():
            raise ConfigurationError(f"OAuth client secrets not found: {self._client_secrets}")

        creds: Any | None = None
        raw = self._store.load()
        if raw:
            try:
                info = json.loads(raw)
                # Do NOT pass newly requested scopes here — that would make the
                # Credentials object claim scopes the token was never granted.
                # Installed apps do not support incremental authorization.
                creds = Credentials.from_authorized_user_info(info)  # type: ignore[no-untyped-call]
            except Exception:
                logger.debug("Cached OAuth token could not be loaded; reauthorizing")
                creds = None

        if creds is not None and not self._token_covers_required(creds):
            logger.debug(
                "Cached OAuth token lacks required scopes; reauthorizing "
                "(installed apps do not support incremental authorization)"
            )
            creds = None

        if creds and creds.valid:
            return creds

        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                if not self._token_covers_required(creds):
                    creds = None
                else:
                    self._persist(creds)
                    return creds
            except Exception as exc:
                logger.debug("OAuth refresh failed; starting browser flow: %s", type(exc).__name__)
                creds = None

        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self._client_secrets),
                list(self._scopes.values),
            )
            creds = flow.run_local_server(port=0)
        except Exception as exc:
            raise AuthenticationError(
                f"OAuth authorization failed or was cancelled: {exc}"
            ) from exc

        self._persist(creds)
        return creds

    def _token_covers_required(self, creds: Any) -> bool:
        """Return True when the stored/token scopes cover the requested set."""
        granted = _granted_scopes(creds)
        if not granted:
            # Some token files omit scopes; do not assume the new request was granted.
            return False
        return self._scopes.values <= granted

    def _persist(self, creds: Any) -> None:
        try:
            self._store.save(creds.to_json())
        except Exception:
            logger.debug("Unable to persist OAuth token (non-fatal)")


def _granted_scopes(creds: Any) -> frozenset[str]:
    raw = getattr(creds, "scopes", None)
    if not raw:
        return frozenset()
    if isinstance(raw, str):
        return frozenset(s for s in raw.split() if s)
    return frozenset(str(s) for s in raw)
