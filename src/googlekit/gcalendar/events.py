"""Events manager — list, create, update, patch, delete."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime
from typing import Any

from googlekit.core.exceptions import ValidationError
from googlekit.core.pagination import Page, PageIterator
from googlekit.core.transport import Transport
from googlekit.core.types import CalendarId, EventId
from googlekit.core.validation import require_non_empty
from googlekit.gcalendar._datetime import ensure_aware, to_rfc3339
from googlekit.gcalendar._payload import apply_event_fields, build_create_body
from googlekit.gcalendar.models import Attendee, Event, Reminders, SendUpdates


class EventsManager:
    """Calendar events operations."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def _service(self) -> Any:
        return self._transport.get_service("calendar", "v3")

    def _default_tz(self) -> str | None:
        return self._transport.config.default_timezone

    def list(
        self,
        calendar_id: CalendarId = "primary",
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
        """List events (one page). Time bounds must be timezone-aware."""
        cid = require_non_empty(calendar_id, "calendar_id")
        kwargs: dict[str, Any] = {
            "calendarId": cid,
            "maxResults": page_size,
            "singleEvents": single_events,
            "showDeleted": show_deleted,
        }
        if page_token:
            kwargs["pageToken"] = page_token
        if sync_token:
            kwargs["syncToken"] = sync_token
        else:
            if time_min is not None:
                aware = ensure_aware(time_min, default_timezone=self._default_tz(), name="time_min")
                kwargs["timeMin"] = to_rfc3339(aware)
            if time_max is not None:
                aware = ensure_aware(time_max, default_timezone=self._default_tz(), name="time_max")
                kwargs["timeMax"] = to_rfc3339(aware)
            if order_by and single_events:
                kwargs["orderBy"] = order_by
            if q:
                kwargs["q"] = q
            if time_zone:
                kwargs["timeZone"] = time_zone
        request = self._service().events().list(**kwargs)
        data = self._transport.execute(request)
        items = [Event.from_api(e) for e in data.get("items") or []]
        return Page(items=items, next_page_token=data.get("nextPageToken"), raw=data)

    def iterate(
        self,
        calendar_id: CalendarId = "primary",
        *,
        time_min: datetime | None = None,
        time_max: datetime | None = None,
        page_size: int = 100,
        single_events: bool = True,
        order_by: str | None = "startTime",
        q: str | None = None,
        show_deleted: bool = False,
        time_zone: str | None = None,
    ) -> PageIterator[Event]:
        """Lazily iterate all matching events."""

        def fetch(token: str | None, size: int) -> Page[Event]:
            return self.list(
                calendar_id,
                time_min=time_min,
                time_max=time_max,
                page_size=size,
                page_token=token,
                single_events=single_events,
                order_by=order_by,
                q=q,
                show_deleted=show_deleted,
                time_zone=time_zone,
            )

        return PageIterator(fetch, page_size=page_size)

    def get(self, calendar_id: CalendarId, event_id: EventId) -> Event:
        """Get a single event."""
        cid = require_non_empty(calendar_id, "calendar_id")
        eid = require_non_empty(event_id, "event_id")
        request = self._service().events().get(calendarId=cid, eventId=eid)
        data = self._transport.execute(request)
        return Event.from_api(data)

    def create(
        self,
        calendar_id: CalendarId = "primary",
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
        """Create an event.

        Timed events require timezone-aware datetimes (or
        ``ClientConfig.default_timezone``). ``send_updates`` defaults to
        ``none`` so invitations are not emailed unless requested.
        """
        cid = require_non_empty(calendar_id, "calendar_id")
        require_non_empty(summary, "summary")
        body = build_create_body(
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
            default_timezone=self._default_tz(),
            transparency=transparency,
            visibility=visibility,
            color_id=color_id,
            extended_properties=extended_properties,
            conference=conference,
            status=status,
        )
        kwargs: dict[str, Any] = {
            "calendarId": cid,
            "body": body,
            "sendUpdates": str(send_updates),
        }
        if conference:
            kwargs["conferenceDataVersion"] = 1
        request = self._service().events().insert(**kwargs)
        data = self._transport.execute(request)
        return Event.from_api(data)

    def update(
        self,
        calendar_id: CalendarId,
        event_id: EventId,
        *,
        summary: str | None = None,
        start: datetime | date | None = None,
        end: datetime | date | None = None,
        description: str | None = None,
        location: str | None = None,
        attendees: Sequence[Attendee | str] | None = None,
        reminders: Reminders | None = None,
        recurrence: Sequence[str] | None = None,
        all_day: bool | None = None,
        time_zone: str | None = None,
        transparency: str | None = None,
        visibility: str | None = None,
        send_updates: SendUpdates | str = SendUpdates.NONE,
        conference: bool = False,
        status: str | None = None,
    ) -> Event:
        """Full update: fetch, merge fields, then events.update."""
        existing = self.get(calendar_id, event_id)
        body = dict(existing.raw)
        apply_event_fields(
            body,
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
            default_timezone=self._default_tz(),
            transparency=transparency,
            visibility=visibility,
            status=status,
            conference=conference,
        )
        kwargs: dict[str, Any] = {
            "calendarId": calendar_id,
            "eventId": event_id,
            "body": body,
            "sendUpdates": str(send_updates),
        }
        if conference:
            kwargs["conferenceDataVersion"] = 1
        request = self._service().events().update(**kwargs)
        data = self._transport.execute(request)
        return Event.from_api(data)

    def patch(
        self,
        calendar_id: CalendarId,
        event_id: EventId,
        *,
        summary: str | None = None,
        start: datetime | date | None = None,
        end: datetime | date | None = None,
        description: str | None = None,
        location: str | None = None,
        attendees: Sequence[Attendee | str] | None = None,
        reminders: Reminders | None = None,
        recurrence: Sequence[str] | None = None,
        all_day: bool | None = None,
        time_zone: str | None = None,
        transparency: str | None = None,
        visibility: str | None = None,
        send_updates: SendUpdates | str = SendUpdates.NONE,
        conference: bool = False,
        status: str | None = None,
        response_status: str | None = None,
    ) -> Event:
        """Partial update via events.patch."""
        cid = require_non_empty(calendar_id, "calendar_id")
        eid = require_non_empty(event_id, "event_id")
        body: dict[str, Any] = {}
        apply_event_fields(
            body,
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
            default_timezone=self._default_tz(),
            transparency=transparency,
            visibility=visibility,
            status=status,
            conference=conference,
        )
        if response_status is not None:
            if attendees is None:
                raise ValidationError("response_status requires attendees including self")
            for attendee in body.get("attendees") or []:
                attendee["responseStatus"] = response_status
        kwargs: dict[str, Any] = {
            "calendarId": cid,
            "eventId": eid,
            "body": body,
            "sendUpdates": str(send_updates),
        }
        if conference:
            kwargs["conferenceDataVersion"] = 1
        request = self._service().events().patch(**kwargs)
        data = self._transport.execute(request)
        return Event.from_api(data)

    def delete(
        self,
        calendar_id: CalendarId,
        event_id: EventId,
        *,
        send_updates: SendUpdates | str = SendUpdates.NONE,
    ) -> None:
        """Delete an event. ``send_updates`` defaults to ``none``."""
        cid = require_non_empty(calendar_id, "calendar_id")
        eid = require_non_empty(event_id, "event_id")
        request = (
            self._service()
            .events()
            .delete(calendarId=cid, eventId=eid, sendUpdates=str(send_updates))
        )
        self._transport.execute(request)
