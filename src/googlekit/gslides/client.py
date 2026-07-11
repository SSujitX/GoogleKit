"""Google Slides client."""

from __future__ import annotations

from pathlib import Path

from googlekit.auth.adc import ADCCredentialProvider
from googlekit.auth.oauth import OAuthCredentialProvider
from googlekit.auth.scopes import ScopeProfile, ScopeSet, preset_for
from googlekit.auth.service_account import ServiceAccountCredentialProvider
from googlekit.core.configuration import ClientConfig
from googlekit.core.protocols import CredentialProvider
from googlekit.core.service_apis import SlidesAPI
from googlekit.core.transport import Transport
from googlekit.gslides.elements import ElementsManager
from googlekit.gslides.images import ImagesManager
from googlekit.gslides.models import BatchUpdateResult, PredefinedLayout, Presentation
from googlekit.gslides.pages import PagesManager
from googlekit.gslides.presentations import PresentationsManager
from googlekit.gslides.tables import TablesManager
from googlekit.gslides.text import TextManager


class SlidesClient:
    """High-level Google Slides API client.

    Managers: ``presentations``, ``pages``, ``elements``, ``text``, ``images``, ``tables``.

    Shortcuts: ``create_presentation``, ``get_presentation``, ``add_slide``.

    Sizes/transforms use EMU helpers on models. Export/share need Drive scopes.
    """

    def __init__(
        self,
        provider: CredentialProvider,
        *,
        config: ClientConfig | None = None,
    ) -> None:
        self._provider = provider
        self._config = config or ClientConfig()
        self._transport = Transport(provider, self._config, extra="gslides")
        self.presentations = PresentationsManager(self._transport)
        self.pages = PagesManager(self._transport)
        self.elements = ElementsManager(self._transport)
        self.text = TextManager(self._transport)
        self.images = ImagesManager(self._transport)
        self.tables = TablesManager(self._transport)

    def create_presentation(self, title: str = "Untitled presentation") -> Presentation:
        """Create a new blank presentation."""
        return self.presentations.create(title)

    def get_presentation(self, presentation_id: str) -> Presentation:
        """Fetch a presentation including slides."""
        return self.presentations.get(presentation_id)

    def add_slide(
        self,
        presentation_id: str,
        *,
        layout: PredefinedLayout | str = PredefinedLayout.BLANK,
        insertion_index: int | None = None,
        object_id: str | None = None,
    ) -> BatchUpdateResult:
        """Add a slide with a predefined layout.

        Args:
            presentation_id: Presentation ID.
            layout: Predefined layout name (default blank).
            insertion_index: Zero-based index; append when omitted.
            object_id: Optional stable object ID for the new slide.
        """
        return self.pages.add(
            presentation_id,
            layout=layout,
            insertion_index=insertion_index,
            object_id=object_id,
        )

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
    ) -> SlidesAPI:
        """Create a Slides client using desktop OAuth."""
        scope_set = _resolve_scopes(scopes, profile)
        provider = OAuthCredentialProvider(
            client_secrets,
            scopes=scope_set,
            token_path=token_path,
            extra="gslides",
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
    ) -> SlidesAPI:
        """Create a Slides client using a service-account JSON key."""
        scope_set = _resolve_scopes(scopes, profile)
        provider = ServiceAccountCredentialProvider(
            credentials_file,
            scopes=scope_set,
            subject=subject,
            extra="gslides",
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
    ) -> SlidesAPI:
        """Create a Slides client using Application Default Credentials."""
        scope_set = _resolve_scopes(scopes, profile)
        provider = ADCCredentialProvider(
            scopes=scope_set,
            quota_project_id=quota_project_id,
            extra="gslides",
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
    return preset_for("gslides", profile)
