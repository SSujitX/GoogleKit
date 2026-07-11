"""Build Calendar event request bodies."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime
from typing import Any
from uuid import uuid4

from googlekit.core.exceptions import ValidationError
from googlekit.core.validation import require_non_empty
from googlekit.gcalendar._datetime import event_time_body
from googlekit.gcalendar.models import Attendee, Reminders


def attendees_payload(attendees: Sequence[Attendee | str]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in attendees:
        if isinstance(item, str):
            require_non_empty(item, "attendee email")
            result.append({"email": item})
        else:
            result.append(item.to_api())
    return result


def apply_event_fields(
    body: dict[str, Any],
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
    default_timezone: str | None = None,
    transparency: str | None = None,
    visibility: str | None = None,
    status: str | None = None,
    conference: bool = False,
) -> None:
    """Mutate ``body`` with provided event fields."""
    if summary is not None:
        body["summary"] = summary
    if description is not None:
        body["description"] = description
    if location is not None:
        body["location"] = location
    if attendees is not None:
        body["attendees"] = attendees_payload(attendees)
    if reminders is not None:
        body["reminders"] = reminders.to_api()
    if recurrence is not None:
        body["recurrence"] = list(recurrence)
    if transparency is not None:
        body["transparency"] = transparency
    if visibility is not None:
        body["visibility"] = visibility
    if status is not None:
        body["status"] = status
    if start is not None or end is not None:
        if start is None or end is None:
            raise ValidationError("Provide both start and end when updating time")
        start_body, end_body = event_time_body(
            start=start,
            end=end,
            time_zone=time_zone,
            default_timezone=default_timezone,
            all_day=all_day,
        )
        body["start"] = start_body
        body["end"] = end_body
    if conference:
        body["conferenceData"] = {
            "createRequest": {
                "requestId": uuid4().hex,
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        }


def build_create_body(
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
    default_timezone: str | None = None,
    transparency: str | None = None,
    visibility: str | None = None,
    color_id: str | None = None,
    extended_properties: dict[str, Any] | None = None,
    conference: bool = False,
    status: str | None = None,
) -> dict[str, Any]:
    """Build an events.insert body."""
    start_body, end_body = event_time_body(
        start=start,
        end=end,
        time_zone=time_zone,
        default_timezone=default_timezone,
        all_day=all_day,
    )
    body: dict[str, Any] = {
        "summary": summary,
        "start": start_body,
        "end": end_body,
    }
    apply_event_fields(
        body,
        description=description,
        location=location,
        attendees=attendees,
        reminders=reminders,
        recurrence=recurrence,
        transparency=transparency,
        visibility=visibility,
        status=status,
        conference=conference,
        default_timezone=default_timezone,
    )
    if color_id:
        body["colorId"] = color_id
    if extended_properties:
        body["extendedProperties"] = extended_properties
    return body
