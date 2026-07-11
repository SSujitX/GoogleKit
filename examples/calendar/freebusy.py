"""Query free/busy intervals for one or more calendars."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from googlekit.gcalendar import CalendarClient

client = CalendarClient.from_adc()

time_min = datetime.now(UTC)
time_max = time_min + timedelta(days=7)

result = client.freebusy.query(
    ["primary"],
    time_min,
    time_max,
    time_zone="UTC",
)

print(f"Window: {result.time_min.isoformat()} -> {result.time_max.isoformat()}")
for calendar_id, intervals in result.calendars.items():
    print(f"Calendar {calendar_id}: {len(intervals)} busy block(s)")
    for busy in intervals:
        print(f"  {busy.start.isoformat()} - {busy.end.isoformat()}")
