"""Calendars manager — list, get, create, update, delete."""

from __future__ import annotations

from typing import Any

from googlekit.core.pagination import Page, PageIterator
from googlekit.core.transport import Transport
from googlekit.core.types import CalendarId
from googlekit.core.validation import require_non_empty
from googlekit.gcalendar.models import Calendar


class CalendarsManager:
    """CalendarList and calendars resource operations."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def _service(self) -> Any:
        return self._transport.get_service("calendar", "v3")

    def list(
        self,
        *,
        page_size: int = 100,
        page_token: str | None = None,
        show_deleted: bool = False,
        show_hidden: bool = False,
        min_access_role: str | None = None,
    ) -> Page[Calendar]:
        """List calendars from the user's calendar list (one page)."""
        kwargs: dict[str, Any] = {
            "maxResults": page_size,
            "showDeleted": show_deleted,
            "showHidden": show_hidden,
        }
        if page_token:
            kwargs["pageToken"] = page_token
        if min_access_role:
            kwargs["minAccessRole"] = min_access_role
        request = self._service().calendarList().list(**kwargs)
        data = self._transport.execute(request)
        items = [Calendar.from_api(c) for c in data.get("items") or []]
        return Page(
            items=items,
            next_page_token=data.get("nextPageToken"),
            raw=data,
        )

    def iterate(
        self,
        *,
        page_size: int = 100,
        show_deleted: bool = False,
        show_hidden: bool = False,
        min_access_role: str | None = None,
    ) -> PageIterator[Calendar]:
        """Lazily iterate all calendars in the calendar list."""

        def fetch(token: str | None, size: int) -> Page[Calendar]:
            return self.list(
                page_size=size,
                page_token=token,
                show_deleted=show_deleted,
                show_hidden=show_hidden,
                min_access_role=min_access_role,
            )

        return PageIterator(fetch, page_size=page_size)

    def get(self, calendar_id: CalendarId) -> Calendar:
        """Get a calendar by ID (calendars.get)."""
        cid = require_non_empty(calendar_id, "calendar_id")
        request = self._service().calendars().get(calendarId=cid)
        data = self._transport.execute(request)
        return Calendar.from_api(data)

    def create(
        self,
        summary: str,
        *,
        description: str | None = None,
        time_zone: str | None = None,
        location: str | None = None,
    ) -> Calendar:
        """Create a secondary calendar.

        Args:
            summary: Calendar title.
            description: Optional description.
            time_zone: IANA time zone for the calendar.
            location: Optional geographic location string.

        Returns:
            The created calendar.
        """
        require_non_empty(summary, "summary")
        body: dict[str, Any] = {"summary": summary}
        if description is not None:
            body["description"] = description
        tz = time_zone or self._transport.config.default_timezone
        if tz:
            body["timeZone"] = tz
        if location is not None:
            body["location"] = location
        request = self._service().calendars().insert(body=body)
        data = self._transport.execute(request)
        return Calendar.from_api(data)

    def update(
        self,
        calendar_id: CalendarId,
        *,
        summary: str | None = None,
        description: str | None = None,
        time_zone: str | None = None,
        location: str | None = None,
    ) -> Calendar:
        """Update calendar metadata (calendars.patch)."""
        cid = require_non_empty(calendar_id, "calendar_id")
        body: dict[str, Any] = {}
        if summary is not None:
            body["summary"] = summary
        if description is not None:
            body["description"] = description
        if time_zone is not None:
            body["timeZone"] = time_zone
        if location is not None:
            body["location"] = location
        request = self._service().calendars().patch(calendarId=cid, body=body)
        data = self._transport.execute(request)
        return Calendar.from_api(data)

    def delete(self, calendar_id: CalendarId) -> None:
        """Delete a secondary calendar.

        Note:
            Primary calendars cannot be deleted via the API.
        """
        cid = require_non_empty(calendar_id, "calendar_id")
        request = self._service().calendars().delete(calendarId=cid)
        self._transport.execute(request)
