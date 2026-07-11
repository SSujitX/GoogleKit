"""Google Calendar client."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime
from pathlib import Path
from typing import Any

from googlekit.auth.adc import ADCCredentialProvider
from googlekit.auth.oauth import OAuthCredentialProvider
from googlekit.auth.scopes import ScopeProfile, ScopeSet, preset_for
from googlekit.auth.service_account import ServiceAccountCredentialProvider
from googlekit.core.configuration import ClientConfig
from googlekit.core.pagination import Page
from googlekit.core.protocols import CredentialProvider
from googlekit.core.service_apis import CalendarAPI
from googlekit.core.transport import Transport
from googlekit.gcalendar.calendars import CalendarsManager
from googlekit.gcalendar.events import EventsManager
from googlekit.gcalendar.freebusy import FreeBusyManager
from googlekit.gcalendar.models import Attendee, Event, Reminders, SendUpdates


class CalendarClient:
    """High-level Google Calendar API client.

    Managers: ``calendars``, ``events``, ``freebusy``.

    Shortcuts: ``list_events``, ``create_event``, ``get_event``, ``delete_event``.

    Timed events need timezone-aware datetimes or
    ``ClientConfig(default_timezone="...")``.
    """

    def __init__(
        self,
        provider: CredentialProvider,
        *,
        config: ClientConfig | None = None,
    ) -> None:
        self._provider = provider
        self._config = config or ClientConfig()
        self._transport = Transport(provider, self._config, extra="gcalendar")
        self.calendars = CalendarsManager(self._transport)
        self.events = EventsManager(self._transport)
        self.freebusy = FreeBusyManager(self._transport)

    def list_events(
        self,
        calendar_id: str = "primary",
        *,
        time_min: datetime | None = None,
        time_max: datetime | None = None,
        page_size: int = 100,
        page_token: str | None = None,
        single_events: bool = True,
        order_by: str | None = "startTime",
        q: str | None = None,
        sync_token: str | None = None,
        show_deleted: bool = False,
        time_zone: str | None = None,
    ) -> Page[Event]:
        """List events (one page). Timed bounds must be timezone-aware.

        Args:
            calendar_id: Calendar id (default ``primary``).
            time_min / time_max: Inclusive window (timezone-aware datetimes).
            page_size: Max events in this page.
            q: Free-text search query.
        """
        return self.events.list(
            calendar_id,
            time_min=time_min,
            time_max=time_max,
            page_size=page_size,
            page_token=page_token,
            single_events=single_events,
            order_by=order_by,
            q=q,
            sync_token=sync_token,
            show_deleted=show_deleted,
            time_zone=time_zone,
        )

    def create_event(
        self,
        calendar_id: str = "primary",
        *,
        summary: str,
        start: datetime | date,
        end: datetime | date,
        description: str | None = None,
        location: str | None = None,
        attendees: Sequence[Attendee | str] | None = None,
        reminders: Reminders | None = None,
        recurrence: Sequence[str] | None = None,
        all_day: bool | None = None,
        time_zone: str | None = None,
        transparency: str | None = None,
        visibility: str | None = None,
        color_id: str | None = None,
        extended_properties: dict[str, Any] | None = None,
        conference: bool = False,
        send_updates: SendUpdates | str = SendUpdates.NONE,
        status: str | None = None,
    ) -> Event:
        """Create an event on ``calendar_id`` (default primary).

        Timed events require timezone-aware datetimes (or
        ``ClientConfig.default_timezone``). ``send_updates`` defaults to
        ``none`` so invitations are not emailed unless requested.
        """
        return self.events.create(
            calendar_id,
            summary=summary,
            start=start,
            end=end,
            description=description,
            location=location,
            attendees=attendees,
            reminders=reminders,
            recurrence=recurrence,
            all_day=all_day,
            time_zone=time_zone,
            transparency=transparency,
            visibility=visibility,
            color_id=color_id,
            extended_properties=extended_properties,
            conference=conference,
            send_updates=send_updates,
            status=status,
        )

    def get_event(self, calendar_id: str, event_id: str) -> Event:
        """Get a single event."""
        return self.events.get(calendar_id, event_id)

    def delete_event(
        self,
        calendar_id: str,
        event_id: str,
        *,
        send_updates: SendUpdates | str = SendUpdates.NONE,
    ) -> None:
        """Delete an event. ``send_updates`` defaults to ``none``."""
        self.events.delete(calendar_id, event_id, send_updates=send_updates)

    @property
    def provider(self) -> CredentialProvider:
        """Credential provider backing this client (advanced)."""
        return self._provider

    @property
    def config(self) -> ClientConfig:
        """Runtime config (timeout, retry, default_timezone, …)."""
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
    ) -> CalendarAPI:
        """Create a Calendar client using desktop OAuth."""
        scope_set = _resolve_scopes(scopes, profile)
        provider = OAuthCredentialProvider(
            client_secrets,
            scopes=scope_set,
            token_path=token_path,
            extra="gcalendar",
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
    ) -> CalendarAPI:
        """Create a Calendar client using a service-account JSON key."""
        scope_set = _resolve_scopes(scopes, profile)
        provider = ServiceAccountCredentialProvider(
            credentials_file,
            scopes=scope_set,
            subject=subject,
            extra="gcalendar",
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
    ) -> CalendarAPI:
        """Create a Calendar client using Application Default Credentials."""
        scope_set = _resolve_scopes(scopes, profile)
        provider = ADCCredentialProvider(
            scopes=scope_set,
            quota_project_id=quota_project_id,
            extra="gcalendar",
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
    return preset_for("gcalendar", profile)
