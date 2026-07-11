"""Application Default Credentials provider."""

from __future__ import annotations

from typing import Any

from googlekit.auth.scopes import ScopeSet
from googlekit.core.exceptions import AuthenticationError
from googlekit.core.optional import require_extra


class ADCCredentialProvider:
    """Use Application Default Credentials (gcloud / env / metadata)."""

    def __init__(
        self,
        *,
        scopes: ScopeSet,
        quota_project_id: str | None = None,
        extra: str = "gdrive",
    ) -> None:
        self._scopes = scopes
        self._quota_project_id = quota_project_id
        self._extra = extra
        self._credentials: Any | None = None

    def scopes(self) -> frozenset[str]:
        return self._scopes.values

    def credentials(self) -> Any:
        if self._credentials is not None:
            return self._credentials
        require_extra(self._extra)
        import google.auth

        try:
            creds, _project = google.auth.default(scopes=list(self._scopes.values))
            if self._quota_project_id and hasattr(creds, "with_quota_project"):
                creds = creds.with_quota_project(self._quota_project_id)
            self._credentials = creds
            return creds
        except Exception as exc:
            raise AuthenticationError(
                "Application Default Credentials are unavailable. "
                "Run: gcloud auth application-default login "
                "or set GOOGLE_APPLICATION_CREDENTIALS."
            ) from exc
