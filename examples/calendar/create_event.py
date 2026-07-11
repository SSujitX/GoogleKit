"""Create a timed Calendar event with attendees and optional Meet link."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from googlekit.core.configuration import ClientConfig
from googlekit.gcalendar import CalendarClient, SendUpdates

# default_timezone lets callers pass naive local times safely when desired.
config = ClientConfig(default_timezone="UTC")
client = CalendarClient.from_adc(config=config)

start = datetime.now(UTC) + timedelta(days=1)
start = start.replace(minute=0, second=0, microsecond=0)
end = start + timedelta(hours=1)

event = client.events.create(
    "primary",
    summary="GoogleKit planning",
    start=start,
    end=end,
    description="Discuss Sheets + Calendar SDK surface.",
    location="Virtual",
    attendees=["teammate@example.com"],
    conference=True,
    # Explicit: do not email attendees unless you pass SendUpdates.ALL
    send_updates=SendUpdates.NONE,
)

print(f"Created event {event.id}")
print(f"Meet / hangout: {event.hangout_link}")
print(f"HTML link: {event.html_link}")
