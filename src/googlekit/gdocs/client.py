"""Google Docs client."""

from __future__ import annotations

from pathlib import Path

from googlekit.auth.adc import ADCCredentialProvider
from googlekit.auth.oauth import OAuthCredentialProvider
from googlekit.auth.scopes import ScopeProfile, ScopeSet, preset_for
from googlekit.auth.service_account import ServiceAccountCredentialProvider
from googlekit.core.configuration import ClientConfig
from googlekit.core.protocols import CredentialProvider
from googlekit.core.service_apis import DocsAPI
from googlekit.core.transport import Transport
from googlekit.gdocs.content import ContentManager
from googlekit.gdocs.documents import DocumentsManager
from googlekit.gdocs.images import ImagesManager
from googlekit.gdocs.tables import TablesManager


class DocsClient:
    """High-level Google Docs API client.

    Managers: ``documents``, ``content``, ``tables``, ``images``.

    Text indexes are UTF-16 code units. Export/share need Drive scopes
    (request ``gdrive`` yourself — never added silently).
    """

    def __init__(
        self,
        provider: CredentialProvider,
        *,
        config: ClientConfig | None = None,
    ) -> None:
        self._provider = provider
        self._config = config or ClientConfig()
        self._transport = Transport(provider, self._config, extra="gdocs")
        self.documents = DocumentsManager(self._transport)
        self.content = ContentManager(self._transport)
        self.tables = TablesManager(self._transport)
        self.images = ImagesManager(self._transport)

    @property
    def provider(self) -> CredentialProvider:
        """Credential provider backing this client (advanced)."""
        return self._provider

    @property
    def config(self) -> ClientConfig:
        """Runtime config (timeout, retry, …)."""
        return self._config

    @property
    def transport(self) -> Transport:
        """HTTP/discovery transport (advanced / tests)."""
        return self._transport

    @classmethod
    def from_oauth(
        cls,
        client_secrets: str | Path,
        token_path: str | Path | None = None,
        scopes: ScopeSet | list[str] | None = None,
        *,
        profile: ScopeProfile = ScopeProfile.READWRITE,
        config: ClientConfig | None = None,
    ) -> DocsAPI:
        """Create a Docs client using desktop OAuth."""
        scope_set = _resolve_scopes(scopes, profile)
        provider = OAuthCredentialProvider(
            client_secrets,
            scopes=scope_set,
            token_path=token_path,
            extra="gdocs",
        )
        return cls(provider, config=config)

    @classmethod
    def from_service_account(
        cls,
        credentials_file: str | Path,
        subject: str | None = None,
        scopes: ScopeSet | list[str] | None = None,
        *,
        profile: ScopeProfile = ScopeProfile.READWRITE,
        config: ClientConfig | None = None,
    ) -> DocsAPI:
        """Create a Docs client using a service-account JSON key."""
        scope_set = _resolve_scopes(scopes, profile)
        provider = ServiceAccountCredentialProvider(
            credentials_file,
            scopes=scope_set,
            subject=subject,
            extra="gdocs",
        )
        return cls(provider, config=config)

    @classmethod
    def from_adc(
        cls,
        quota_project_id: str | None = None,
        scopes: ScopeSet | list[str] | None = None,
        *,
        profile: ScopeProfile = ScopeProfile.READWRITE,
        config: ClientConfig | None = None,
    ) -> DocsAPI:
        """Create a Docs client using Application Default Credentials."""
        scope_set = _resolve_scopes(scopes, profile)
        provider = ADCCredentialProvider(
            scopes=scope_set,
            quota_project_id=quota_project_id,
            extra="gdocs",
        )
        return cls(provider, config=config)


def _resolve_scopes(
    scopes: ScopeSet | list[str] | None,
    profile: ScopeProfile,
) -> ScopeSet:
    if isinstance(scopes, ScopeSet):
        return scopes
    if scopes is not None:
        return ScopeSet.from_iterable(scopes)
    return preset_for("gdocs", profile)
