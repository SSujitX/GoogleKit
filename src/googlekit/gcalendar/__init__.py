"""Google Calendar service package."""

from __future__ import annotations

from googlekit.gcalendar.client import CalendarClient
from googlekit.gcalendar.models import (
    Attendee,
    BusyInterval,
    Calendar,
    ConferenceData,
    Event,
    EventDateTime,
    EventStatus,
    EventTransparency,
    EventVisibility,
    FreeBusyResponse,
    ReminderOverride,
    Reminders,
    SendUpdates,
)

__all__ = [
    "Attendee",
    "BusyInterval",
    "Calendar",
    "CalendarClient",
    "ConferenceData",
    "Event",
    "EventDateTime",
    "EventStatus",
    "EventTransparency",
    "EventVisibility",
    "FreeBusyResponse",
    "ReminderOverride",
    "Reminders",
    "SendUpdates",
]
