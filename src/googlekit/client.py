"""Unified GoogleKit client with lazy service accessors."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from googlekit.auth.adc import ADCCredentialProvider
from googlekit.auth.credentials import build_provider
from googlekit.auth.oauth import OAuthCredentialProvider
from googlekit.auth.scopes import ScopeProfile, ScopeSet, aggregate_scopes, preset_for
from googlekit.auth.service_account import ServiceAccountCredentialProvider
from googlekit.core.configuration import ClientConfig
from googlekit.core.protocols import CredentialProvider

if TYPE_CHECKING:
    from googlekit.gcalendar.client import CalendarClient
    from googlekit.gdocs.client import DocsClient
    from googlekit.gdrive.client import DriveClient
    from googlekit.gsheets.client import SheetsClient
    from googlekit.gslides.client import SlidesClient


class GoogleKit:
    """Unified entry point for Drive, Sheets, Calendar, Docs, and Slides.

    Services are initialized lazily on first access so importing GoogleKit does
    not pull in every Google API client.
    """

    def __init__(
        self,
        provider: CredentialProvider,
        *,
        config: ClientConfig | None = None,
        scopes: ScopeSet | None = None,
    ) -> None:
        self._provider = provider
        self._config = config or ClientConfig()
        self._scopes = scopes or ScopeSet(provider.scopes())
        self._drive: DriveClient | None = None
        self._sheets: SheetsClient | None = None
        self._calendar: CalendarClient | None = None
        self._docs: DocsClient | None = None
        self._slides: SlidesClient | None = None

    @classmethod
    def from_oauth(
        cls,
        client_secrets: str | Path,
        token_path: str | Path | None = None,
        scopes: ScopeSet | list[str] | None = None,
        *,
        services: list[str] | None = None,
        profile: ScopeProfile = ScopeProfile.READWRITE,
        config: ClientConfig | None = None,
    ) -> GoogleKit:
        """Create a client using desktop OAuth client secrets."""
        scope_set = _resolve_scopes(scopes, services, profile)
        provider = OAuthCredentialProvider(
            client_secrets,
            scopes=scope_set,
            token_path=token_path,
            extra=_primary_extra(services),
        )
        return cls(provider, config=config, scopes=scope_set)

    @classmethod
    def from_service_account(
        cls,
        credentials_file: str | Path,
        subject: str | None = None,
        scopes: ScopeSet | list[str] | None = None,
        *,
        services: list[str] | None = None,
        profile: ScopeProfile = ScopeProfile.READWRITE,
        config: ClientConfig | None = None,
    ) -> GoogleKit:
        """Create a client using a service-account JSON key."""
        scope_set = _resolve_scopes(scopes, services, profile)
        provider = ServiceAccountCredentialProvider(
            credentials_file,
            scopes=scope_set,
            subject=subject,
            extra=_primary_extra(services),
        )
        return cls(provider, config=config, scopes=scope_set)

    @classmethod
    def from_adc(
        cls,
        quota_project_id: str | None = None,
        scopes: ScopeSet | list[str] | None = None,
        *,
        services: list[str] | None = None,
        profile: ScopeProfile = ScopeProfile.READWRITE,
        config: ClientConfig | None = None,
    ) -> GoogleKit:
        """Create a client using Application Default Credentials."""
        scope_set = _resolve_scopes(scopes, services, profile)
        provider = ADCCredentialProvider(
            scopes=scope_set,
            quota_project_id=quota_project_id,
            extra=_primary_extra(services),
        )
        return cls(provider, config=config, scopes=scope_set)

    @classmethod
    def auto(
        cls,
        *,
        services: list[str] | None = None,
        profile: ScopeProfile = ScopeProfile.READWRITE,
        config: ClientConfig | None = None,
    ) -> GoogleKit:
        """Auto-detect ADC or local credential files (PyDrive4-style)."""
        scope_set = _resolve_scopes(None, services, profile)
        provider = build_provider(
            method="auto",
            scopes=scope_set,
            services=services,
            profile=profile,
            extra=_primary_extra(services),
        )
        return cls(provider, config=config, scopes=scope_set)

    @property
    def provider(self) -> CredentialProvider:
        return self._provider

    @property
    def config(self) -> ClientConfig:
        return self._config

    @property
    def scopes(self) -> ScopeSet:
        return self._scopes

    @property
    def drive(self) -> DriveClient:
        if self._drive is None:
            from googlekit.gdrive.client import DriveClient

            self._drive = DriveClient(self._provider, config=self._config)
        return self._drive

    @property
    def sheets(self) -> SheetsClient:
        if self._sheets is None:
            from googlekit.gsheets.client import SheetsClient

            self._sheets = SheetsClient(self._provider, config=self._config)
        return self._sheets

    @property
    def calendar(self) -> CalendarClient:
        if self._calendar is None:
            from googlekit.gcalendar.client import CalendarClient

            self._calendar = CalendarClient(self._provider, config=self._config)
        return self._calendar

    @property
    def docs(self) -> DocsClient:
        if self._docs is None:
            from googlekit.gdocs.client import DocsClient

            self._docs = DocsClient(self._provider, config=self._config)
        return self._docs

    @property
    def slides(self) -> SlidesClient:
        if self._slides is None:
            from googlekit.gslides.client import SlidesClient

            self._slides = SlidesClient(self._provider, config=self._config)
        return self._slides


def _resolve_scopes(
    scopes: ScopeSet | list[str] | None,
    services: list[str] | None,
    profile: ScopeProfile,
) -> ScopeSet:
    if isinstance(scopes, ScopeSet):
        return scopes
    if scopes is not None:
        return ScopeSet.from_iterable(scopes)
    if not services:
        from googlekit.core.exceptions import ConfigurationError

        raise ConfigurationError(
            "Pass services=[...] (e.g. services=['gdrive']) or an explicit scopes=... "
            "argument. GoogleKit does not request all Workspace scopes by default."
        )
    return aggregate_scopes(*(preset_for(s, profile) for s in services))


def _primary_extra(services: list[str] | None) -> str:
    if not services:
        return "gdrive"
    mapping = {
        "drive": "gdrive",
        "gdrive": "gdrive",
        "sheets": "gsheets",
        "gsheets": "gsheets",
        "calendar": "gcalendar",
        "gcalendar": "gcalendar",
        "docs": "gdocs",
        "gdocs": "gdocs",
        "slides": "gslides",
        "gslides": "gslides",
    }
    return mapping.get(services[0], "gdrive")


def share_provider(client: GoogleKit) -> CredentialProvider:
    """Return the shared credential provider for cross-service reuse."""
    return client.provider
