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
from googlekit.core.service_apis import (
    CalendarAPI,
    DocsAPI,
    DriveAPI,
    SheetsAPI,
    SlidesAPI,
)

if TYPE_CHECKING:
    from googlekit.gcalendar.client import CalendarClient
    from googlekit.gdocs.client import DocsClient
    from googlekit.gdrive.client import DriveClient
    from googlekit.gsheets.client import SheetsClient
    from googlekit.gslides.client import SlidesClient


class GoogleKit:
    """Unified entry point for Drive, Sheets, Calendar, Docs, and Slides.

    Prefer factory methods (``from_oauth``, ``from_service_account``, ``from_adc``,
    ``auto``). Always pass ``services=[...]`` or explicit ``scopes=`` — GoogleKit
    never requests all Workspace scopes by default.

    Services load lazily on first access (``client.drive``, ``client.sheets``, …).

    Example::

        from googlekit import GoogleKit, ClientConfig, ScopeProfile

        client = GoogleKit.auto(
            services=["gdrive", "gsheets"],
            profile=ScopeProfile.READWRITE,
            config=ClientConfig(retry=5),
        )
        for f in client.drive.files.list(folder_id="root").items:
            print(f.name)
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
        """Create a client with a **Desktop** OAuth client-secrets JSON.

        Args:
            client_secrets: Path to downloaded OAuth client JSON (``installed`` type).
            token_path: Where to cache the user token. Default: ``./token.json``.
            scopes: Explicit scopes, or omit and use ``services`` + ``profile``.
            services: e.g. ``["gdrive", "gsheets"]``. Required unless ``scopes`` is set.
            profile: Least-privilege preset (default ``READWRITE``). For Drive, that is
                ``drive.file`` (app files only) — use ``FULL`` / ``READONLY`` to list all Drive.
            config: Timeouts, retries, timezone, Shared Drive flags, etc.
        """
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
        """Create a client from a service-account JSON key.

        Ordinary service accounts do not see a user's personal Drive unless files are
        shared with the SA email, or you set ``subject`` for Workspace domain-wide
        delegation.
        """
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
        """Create a client using Application Default Credentials.

        Typical local setup: ``gcloud auth application-default login``.
        """
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
        token_path: str | Path | None = None,
    ) -> GoogleKit:
        """Auto-detect credentials: ADC → service-account JSON → OAuth client JSON.

        Looks in the current working directory for common filenames
        (``service_account.json``, ``client_secrets.json``, …).

        When OAuth is used, tokens default to ``./token.json`` unless ``token_path``
        is set. ``services`` (or scopes via other factories) is required.
        """
        scope_set = _resolve_scopes(None, services, profile)
        provider = build_provider(
            method="auto",
            scopes=scope_set,
            services=services,
            profile=profile,
            extra=_primary_extra(services),
            token_path=token_path,
        )
        return cls(provider, config=config, scopes=scope_set)

    @property
    def provider(self) -> CredentialProvider:
        """Underlying credential provider (advanced / cross-client reuse)."""
        return self._provider

    @property
    def config(self) -> ClientConfig:
        """Runtime config (timeout, retry, timezone, Shared Drives, …)."""
        return self._config

    @property
    def scopes(self) -> ScopeSet:
        """OAuth scopes this client was constructed with."""
        return self._scopes

    @property
    def drive(self) -> DriveAPI:
        """Google Drive API — ``files``, ``folders``, ``permissions``, ``changes``."""
        if self._drive is None:
            from googlekit.gdrive.client import DriveClient

            self._drive = DriveClient(self._provider, config=self._config)
        return self._drive

    @property
    def sheets(self) -> SheetsAPI:
        """Google Sheets API — ``spreadsheets``, ``values``, ``worksheets``, ``formatting``."""
        if self._sheets is None:
            from googlekit.gsheets.client import SheetsClient

            self._sheets = SheetsClient(self._provider, config=self._config)
        return self._sheets

    @property
    def calendar(self) -> CalendarAPI:
        """Google Calendar API — ``calendars``, ``events``, ``freebusy``."""
        if self._calendar is None:
            from googlekit.gcalendar.client import CalendarClient

            self._calendar = CalendarClient(self._provider, config=self._config)
        return self._calendar

    @property
    def docs(self) -> DocsAPI:
        """Google Docs API — ``documents``, ``content``, ``tables``, ``images``."""
        if self._docs is None:
            from googlekit.gdocs.client import DocsClient

            self._docs = DocsClient(self._provider, config=self._config)
        return self._docs

    @property
    def slides(self) -> SlidesAPI:
        """Google Slides API — ``presentations``, ``pages``, ``elements``, ``text``, ``images``, ``tables``."""
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
    """Return the shared credential provider for building another service client."""
    return client.provider
