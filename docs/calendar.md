# Google Calendar

Install: `uv add "googlekit[gcalendar]"`

Enable the **Google Calendar API**.

## Client

```python
from googlekit import GoogleKit

kit = GoogleKit.from_oauth("client_secret.json", services=["gcalendar"])
cal = kit.calendar
```

## Managers

| Manager | Role |
| ------- | ---- |
| `calendar.calendars` | List/get/create/update secondary calendars |
| `calendar.events` | CRUD, recurrence, attendees, Meet |
| `calendar.freebusy` | Busy intervals for one or many calendars |

## Intended events API

```python
from datetime import datetime, timezone

cal.events.list("primary", time_min=..., time_max=...)
cal.events.iterate("primary")  # lazy
cal.events.get("primary", event_id)
cal.events.create(
    "primary",
    summary="Sync",
    start=datetime(2026, 8, 1, 15, 0, tzinfo=timezone.utc),
    end=datetime(2026, 8, 1, 16, 0, tzinfo=timezone.utc),
    send_updates="none",  # explicit; do not surprise-email attendees
)
cal.events.update(...)
cal.events.patch(...)
cal.events.delete("primary", event_id, send_updates="none")
```

## Timezones

- Do not accept ambiguous naive datetimes silently
- Prefer timezone-aware `datetime` objects
- All-day events use dates separately from timed events
- Configure `ClientConfig.default_timezone` when you want an explicit default

## Free/busy

```python
intervals = cal.freebusy.query(["primary", "team@example.com"], time_min=..., time_max=...)
```

Returns typed busy intervals.
