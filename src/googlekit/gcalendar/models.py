"""Typed models for Google Calendar."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Any

from googlekit.gcalendar._datetime import parse_api_date, parse_api_datetime


class SendUpdates(StrEnum):
    """Whether to send notifications about event changes."""

    ALL = "all"
    EXTERNAL_ONLY = "externalOnly"
    NONE = "none"


class EventStatus(StrEnum):
    CONFIRMED = "confirmed"
    TENTATIVE = "tentative"
    CANCELLED = "cancelled"


class EventVisibility(StrEnum):
    DEFAULT = "default"
    PUBLIC = "public"
    PRIVATE = "private"
    CONFIDENTIAL = "confidential"


class EventTransparency(StrEnum):
    OPAQUE = "opaque"
    TRANSPARENT = "transparent"


@dataclass(slots=True)
class EventDateTime:
    """Event start or end — either all-day ``date`` or timed ``date_time``."""

    date: date | None = None
    date_time: datetime | None = None
    time_zone: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any] | None) -> EventDateTime | None:
        if not data:
            return None
        dt: datetime | None = None
        d: date | None = None
        if data.get("dateTime"):
            dt = parse_api_datetime(str(data["dateTime"]))
        if data.get("date"):
            d = parse_api_date(str(data["date"]))
        return cls(date=d, date_time=dt, time_zone=data.get("timeZone"), raw=data)

    @property
    def is_all_day(self) -> bool:
        return self.date is not None and self.date_time is None


@dataclass(slots=True)
class Attendee:
    """Event attendee."""

    email: str
    display_name: str | None = None
    optional: bool = False
    response_status: str | None = None
    organizer: bool = False
    self: bool = False
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Attendee:
        return cls(
            email=str(data.get("email", "")),
            display_name=data.get("displayName"),
            optional=bool(data.get("optional", False)),
            response_status=data.get("responseStatus"),
            organizer=bool(data.get("organizer", False)),
            self=bool(data.get("self", False)),
            raw=data,
        )

    def to_api(self) -> dict[str, Any]:
        body: dict[str, Any] = {"email": self.email}
        if self.display_name:
            body["displayName"] = self.display_name
        if self.optional:
            body["optional"] = True
        if self.response_status:
            body["responseStatus"] = self.response_status
        return body


@dataclass(slots=True)
class ReminderOverride:
    method: str
    minutes: int

    def to_api(self) -> dict[str, Any]:
        return {"method": self.method, "minutes": self.minutes}


@dataclass(slots=True)
class Reminders:
    use_default: bool = True
    overrides: list[ReminderOverride] = field(default_factory=list)

    def to_api(self) -> dict[str, Any]:
        body: dict[str, Any] = {"useDefault": self.use_default}
        if self.overrides:
            body["overrides"] = [o.to_api() for o in self.overrides]
        return body

    @classmethod
    def from_api(cls, data: dict[str, Any] | None) -> Reminders | None:
        if not data:
            return None
        overrides = [
            ReminderOverride(method=str(o.get("method", "popup")), minutes=int(o["minutes"]))
            for o in data.get("overrides") or []
            if "minutes" in o
        ]
        return cls(use_default=bool(data.get("useDefault", True)), overrides=overrides)


@dataclass(slots=True)
class ConferenceData:
    """Google Meet / conference metadata."""

    conference_id: str | None = None
    hangout_link: str | None = None
    entry_points: list[dict[str, Any]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any] | None) -> ConferenceData | None:
        if not data:
            return None
        return cls(
            conference_id=data.get("conferenceId"),
            hangout_link=None,
            entry_points=list(data.get("entryPoints") or []),
            raw=data,
        )


@dataclass(slots=True)
class Calendar:
    """CalendarList or calendars resource."""

    id: str
    summary: str
    description: str | None = None
    time_zone: str | None = None
    primary: bool = False
    access_role: str | None = None
    selected: bool = False
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Calendar:
        return cls(
            id=str(data.get("id", "")),
            summary=str(data.get("summary", "")),
            description=data.get("description"),
            time_zone=data.get("timeZone"),
            primary=bool(data.get("primary", False)),
            access_role=data.get("accessRole"),
            selected=bool(data.get("selected", False)),
            raw=data,
        )


@dataclass(slots=True)
class Event:
    """Calendar event."""

    id: str
    summary: str | None = None
    description: str | None = None
    location: str | None = None
    status: str | None = None
    html_link: str | None = None
    hangout_link: str | None = None
    start: EventDateTime | None = None
    end: EventDateTime | None = None
    recurrence: list[str] = field(default_factory=list)
    recurring_event_id: str | None = None
    attendees: list[Attendee] = field(default_factory=list)
    reminders: Reminders | None = None
    conference_data: ConferenceData | None = None
    transparency: str | None = None
    visibility: str | None = None
    color_id: str | None = None
    extended_properties: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Event:
        attendees = [Attendee.from_api(a) for a in data.get("attendees") or []]
        conf = ConferenceData.from_api(data.get("conferenceData"))
        hangout = data.get("hangoutLink")
        if conf is not None and hangout:
            conf = ConferenceData(
                conference_id=conf.conference_id,
                hangout_link=hangout,
                entry_points=conf.entry_points,
                raw=conf.raw,
            )
        return cls(
            id=str(data.get("id", "")),
            summary=data.get("summary"),
            description=data.get("description"),
            location=data.get("location"),
            status=data.get("status"),
            html_link=data.get("htmlLink"),
            hangout_link=hangout,
            start=EventDateTime.from_api(data.get("start")),
            end=EventDateTime.from_api(data.get("end")),
            recurrence=list(data.get("recurrence") or []),
            recurring_event_id=data.get("recurringEventId"),
            attendees=attendees,
            reminders=Reminders.from_api(data.get("reminders")),
            conference_data=conf,
            transparency=data.get("transparency"),
            visibility=data.get("visibility"),
            color_id=data.get("colorId"),
            extended_properties=dict(data.get("extendedProperties") or {}),
            raw=data,
        )


@dataclass(slots=True)
class BusyInterval:
    """A busy time interval for a calendar."""

    calendar_id: str
    start: datetime
    end: datetime
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, calendar_id: str, data: dict[str, Any]) -> BusyInterval:
        return cls(
            calendar_id=calendar_id,
            start=parse_api_datetime(str(data["start"])),
            end=parse_api_datetime(str(data["end"])),
            raw=data,
        )


@dataclass(slots=True)
class FreeBusyResponse:
    """Result of a freeBusy.query call."""

    time_min: datetime
    time_max: datetime
    calendars: dict[str, list[BusyInterval]] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    def all_busy(self) -> list[BusyInterval]:
        items: list[BusyInterval] = []
        for intervals in self.calendars.values():
            items.extend(intervals)
        return items
