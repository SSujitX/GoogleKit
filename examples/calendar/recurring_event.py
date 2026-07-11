"""Create a weekly recurring Calendar event."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from googlekit.gcalendar import CalendarClient, SendUpdates

client = CalendarClient.from_adc()

# Use an explicit offset (or ZoneInfo("America/New_York") when tzdata is available).
tz = timezone(timedelta(hours=-4))
start = datetime(2026, 7, 13, 9, 0, tzinfo=tz)
end = start + timedelta(minutes=30)

event = client.events.create(
    "primary",
    summary="Weekly sync",
    start=start,
    end=end,
    time_zone="America/New_York",
    recurrence=["RRULE:FREQ=WEEKLY;BYDAY=MO;COUNT=8"],
    description="Recurring standup (8 weeks).",
    send_updates=SendUpdates.NONE,
)

print(f"Created recurring event {event.id}")
print("Recurrence:", event.recurrence)
