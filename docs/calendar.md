---
title: Google Calendar API Python client (GoogleKit)
description: >-
  Create and manage Google Calendar events with GoogleKit — Meet links, free/busy,
  sync tokens, attendees, and RSVP via Calendar API v3.
---

# Google Calendar

Install:

```bash
uv add googlekit
```

Enable the **Google Calendar API** in Google Cloud Console.

**Official Google docs:** [Calendar API guides](https://developers.google.com/workspace/calendar/api/guides/overview) ·
[REST reference](https://developers.google.com/workspace/calendar/api/v3/reference) ·
[Events](https://developers.google.com/workspace/calendar/api/v3/reference/events) ·
[Freebusy](https://developers.google.com/workspace/calendar/api/v3/reference/freebusy) ·
[Enable API](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com)

## Client

Use the unified client or `CalendarClient` directly.

```python
from googlekit import GoogleKit
from googlekit.core.configuration import ClientConfig
from googlekit.gcalendar import CalendarClient

# Unified
client = GoogleKit.from_oauth("client_secret.json", services=["gcalendar"])
calendar = client.calendar

# Standalone
calendar = CalendarClient.from_oauth("client_secret.json")
# calendar = CalendarClient.from_service_account("sa.json")
# calendar = CalendarClient.from_adc()

# Optional default IANA zone for naive datetimes
calendar = CalendarClient.from_adc(
    config=ClientConfig(default_timezone="America/New_York"),
)
```

Factory methods accept `profile=ScopeProfile.READWRITE` (default), optional `scopes=`, and `config=`.

### Managers

| Manager | Role |
| ------- | ---- |
| `calendar.calendars` | Calendar list + secondary calendar CRUD |
| `calendar.events` | Event list/CRUD, recurrence, attendees, Meet |
| `calendar.freebusy` | Busy intervals for one or many calendars |

Default **READWRITE** scopes authorize **events + calendars + freebusy** together (see [Scopes](#scopes)).

### Optional shortcuts vs managers

Both appear after `calendar.` (typed as `CalendarAPI`).

| Shortcut | Delegates to |
| -------- | ------------ |
| `list_events(...)` | `events.list(...)` |
| `create_event(..., summary=, start=, end=)` | `events.create(...)` |
| `get_event(calendar_id, event_id)` | `events.get(...)` |
| `delete_event(calendar_id, event_id)` | `events.delete(...)` |

```python
from datetime import UTC, datetime, timedelta

start = datetime.now(UTC)
end = start + timedelta(hours=1)

# Manager
event = calendar.events.create("primary", summary="Standup", start=start, end=end)
# Shortcut (equivalent)
event = calendar.create_event("primary", summary="Standup", start=start, end=end)

page = calendar.list_events("primary", time_min=start)  # or calendar.events.list(...)
```

---

## Timezones and datetimes

Timed events and free/busy windows require **timezone-aware** `datetime` values, or a configured `ClientConfig.default_timezone` so naive values can be localized.

```python
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

# Preferred: aware datetimes
start = datetime(2026, 8, 1, 15, 0, tzinfo=UTC)
end = start + timedelta(hours=1)

# Or ZoneInfo (on Windows, install the `tzdata` package)
start = datetime(2026, 8, 1, 11, 0, tzinfo=ZoneInfo("America/New_York"))
```

Naive datetimes without `default_timezone` raise `ValidationError`.

Helpers used internally (also importable from `googlekit.gcalendar._datetime` if needed):

| Helper | Purpose |
| ------ | ------- |
| `ensure_aware` | Require aware datetime or apply default zone |
| `to_rfc3339` | Serialize to RFC3339 (`Z` for UTC) |
| `event_time_body` | Build API `start` / `end` objects |
| `combine_local_date` | Local date + clock → aware datetime |

---

## All-day events (end exclusive)

All-day events use `date` (not `dateTime`). The Calendar API treats **`end.date` as exclusive**.

A one-day event on 2026-08-01 needs `end = start + 1 day`:

```python
from datetime import date, timedelta

calendar.events.create(
    "primary",
    summary="Company holiday",
    start=date(2026, 8, 1),
    end=date(2026, 8, 2),  # exclusive end
    all_day=True,  # optional when start/end are date objects
)
```

If `end.date <= start.date`, GoogleKit raises `ValidationError` with a clear message. Multi-day spans: start inclusive, end exclusive (Aug 1–3 → end `date(2026, 8, 4)` for three calendar days).

Pass `datetime` values with `all_day=True` to force date-only mode (time components are dropped to dates).

---

## SendUpdates

```python
from googlekit.gcalendar import SendUpdates
```

| Value | Behavior |
| ----- | -------- |
| `SendUpdates.NONE` (`"none"`) | **Default** — do not email guests |
| `SendUpdates.ALL` (`"all"`) | Notify all attendees |
| `SendUpdates.EXTERNAL_ONLY` (`"externalOnly"`) | Notify non-domain guests only |

Create / update / patch / delete all default to `none` so apps never surprise-email attendees.

---

## Models

```python
from googlekit.gcalendar import (
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
```

| Type | Notes |
| ---- | ----- |
| `Calendar` | `id`, `summary`, `description`, `time_zone`, `primary`, `access_role`, `selected` |
| `Event` | `id`, `summary`, `start`/`end` as `EventDateTime`, `attendees`, `reminders`, `conference_data`, `hangout_link`, `recurrence`, `raw` |
| `EventDateTime` | Either `date` (all-day) or `date_time` (timed); `is_all_day` property |
| `Attendee` | `email`, optional `display_name`, `optional`, `response_status`; accepts plain email strings in create/update |
| `Reminders` | `use_default` + `overrides` (`ReminderOverride(method, minutes)`) |
| `ConferenceData` | Meet metadata; `hangout_link` also on `Event` |
| `BusyInterval` / `FreeBusyResponse` | Free/busy results; `FreeBusyResponse.all_busy()` flattens all calendars |

Enums: `EventStatus`, `EventVisibility`, `EventTransparency`, `SendUpdates`.

---

## `calendars` — CalendarsManager

### `list` / `iterate`

```python
page = calendar.calendars.list(
    page_size=100,
    show_deleted=False,
    show_hidden=False,
    min_access_role=None,  # e.g. "writer"
)
for cal in page.items:
    print(cal.id, cal.summary, cal.primary, cal.access_role)

# Lazy pagination
for cal in calendar.calendars.iterate(page_size=50):
    print(cal.summary)
```

### `get`

```python
primary = calendar.calendars.get("primary")
# or a secondary calendar id / email
```

Uses `calendars.get` (not calendarList).

### `create`

Creates a **secondary** calendar:

```python
cal = calendar.calendars.create(
    "Project Apollo",
    description="Launch planning",
    time_zone="UTC",
    location="Remote",
)
print(cal.id)
```

If `time_zone` is omitted, `ClientConfig.default_timezone` is used when set.

### `update`

Partial patch of metadata:

```python
calendar.calendars.update(
    cal.id,
    summary="Project Apollo (archived)",
    description="Done",
    time_zone="America/Los_Angeles",
    location=None,
)
```

### `delete`

```python
calendar.calendars.delete(cal.id)
```

**Primary calendars cannot be deleted** via the API.

---

## `events` — EventsManager

Default `calendar_id` is `"primary"` where applicable.

### `list`

One page of events. Time bounds must be timezone-aware (or covered by `default_timezone`).

```python
from datetime import UTC, datetime, timedelta

page = calendar.events.list(
    "primary",
    time_min=datetime.now(UTC),
    time_max=datetime.now(UTC) + timedelta(days=7),
    page_size=100,
    single_events=True,   # expand recurring instances
    order_by="startTime", # only valid when single_events=True
    q=None,               # free-text search
    show_deleted=False,
    time_zone="UTC",
)
for event in page.items:
    print(event.id, event.summary, event.start)
```

#### Incremental sync (`sync_token`)

When `sync_token` is set, GoogleKit **always forces `showDeleted=True`**. Google rejects incremental sync with `showDeleted=false` (HTTP 400). Incompatible filters (`timeMin` / `timeMax` / `orderBy` / `q`) are **omitted** for that request.

```python
# First full sync: keep nextSyncToken from page.raw
page = calendar.events.list("primary", page_size=250)
sync_token = page.raw.get("nextSyncToken")
# ... store sync_token ...

# Later: only changes (includes cancelled/deleted events)
page = calendar.events.list("primary", sync_token=sync_token)
# show_deleted is forced True internally
for event in page.items:
    if event.status == "cancelled":
        print("deleted/cancelled", event.id)
    else:
        print("upsert", event.id, event.summary)

# Persist page.raw.get("nextSyncToken") for the next round
```

If a stored sync token expires, the API returns 410; clear the token and do a full sync again.

### `iterate`

Lazy pagination over matching events (no `sync_token` path — use `list` for incremental sync):

```python
for event in calendar.events.iterate(
    "primary",
    time_min=datetime.now(UTC),
    time_max=datetime.now(UTC) + timedelta(days=30),
    page_size=100,
    q="standup",
):
    print(event.summary)
```

### `get`

```python
event = calendar.events.get("primary", event_id)
print(event.html_link, event.hangout_link)
```

### `create`

```python
from googlekit.gcalendar import Attendee, Reminders, ReminderOverride, SendUpdates

event = calendar.events.create(
    "primary",
    summary="Planning",
    start=start,
    end=end,
    description="Agenda…",
    location="Virtual",
    attendees=["alice@example.com", Attendee("bob@example.com", optional=True)],
    reminders=Reminders(
        use_default=False,
        overrides=[ReminderOverride(method="popup", minutes=10)],
    ),
    recurrence=None,  # or ["RRULE:FREQ=WEEKLY;BYDAY=MO;COUNT=8"]
    all_day=None,
    time_zone="UTC",
    transparency="opaque",   # or "transparent" (free)
    visibility="default",
    color_id=None,
    extended_properties=None,
    conference=True,         # Google Meet — see below
    send_updates=SendUpdates.NONE,
    status="confirmed",
)
print(event.id, event.hangout_link)
```

#### Google Meet (`conference=True`)

Sets `conferenceDataVersion=1` and a Meet `createRequest`. The returned `Event.hangout_link` / `conference_data` hold the join info.

### `update`

Full update: fetch existing raw body, merge fields, then `events.update`:

```python
event = calendar.events.update(
    "primary",
    event.id,
    summary="Planning (rescheduled)",
    start=new_start,
    end=new_end,
    conference=False,
    send_updates=SendUpdates.ALL,  # notify guests
)
```

When changing times, pass **both** `start` and `end`.

### `patch`

Partial update via `events.patch` (only provided fields):

```python
calendar.events.patch(
    "primary",
    event.id,
    location="Room 12",
    send_updates=SendUpdates.NONE,
)

# RSVP: mark the authenticated attendee with self=True locally
# (Calendar treats attendees[].self as read-only — GoogleKit uses it
# only to identify who to update, then sends email + responseStatus).
from googlekit.gcalendar.models import Attendee

calendar.events.patch(
    "primary",
    event.id,
    attendees=[
        Attendee(email="me@example.com", self=True),
        Attendee(email="guest@example.com"),
    ],
    response_status="accepted",
)
```

### `delete`

```python
calendar.events.delete(
    "primary",
    event.id,
    send_updates=SendUpdates.NONE,
)
```

---

## `freebusy` — FreeBusyManager

### `query`

```python
from datetime import UTC, datetime, timedelta

time_min = datetime.now(UTC)
time_max = time_min + timedelta(days=7)

result = calendar.freebusy.query(
    ["primary", "team@example.com"],
    time_min,
    time_max,
    time_zone="UTC",
)
print(result.time_min, result.time_max)
for calendar_id, intervals in result.calendars.items():
    for busy in intervals:
        print(calendar_id, busy.start, busy.end)

# Flatten
for busy in result.all_busy():
    print(busy.calendar_id, busy.start, busy.end)
```

`time_max` must be after `time_min`. Datetimes follow the same awareness rules as events.

`calendar_ids` may be a single string or a non-empty list.

### `query_one`

```python
intervals = calendar.freebusy.query_one(
    "primary",
    time_min,
    time_max,
    time_zone="UTC",
)
```

Returns `list[BusyInterval]` for that calendar (empty list if none).

---

## Recipes

### Timed meeting with Meet, no emails

```python
from datetime import UTC, datetime, timedelta

from googlekit.gcalendar import CalendarClient, SendUpdates

calendar = CalendarClient.from_adc()
start = datetime.now(UTC).replace(minute=0, second=0, microsecond=0) + timedelta(days=1)
end = start + timedelta(hours=1)

event = calendar.events.create(
    "primary",
    summary="GoogleKit planning",
    start=start,
    end=end,
    attendees=["teammate@example.com"],
    conference=True,
    send_updates=SendUpdates.NONE,
)
print(event.hangout_link)
```

### Weekly recurring event

```python
from datetime import datetime, timedelta, timezone

from googlekit.gcalendar import CalendarClient, SendUpdates

calendar = CalendarClient.from_adc()
tz = timezone(timedelta(hours=-4))
start = datetime(2026, 7, 13, 9, 0, tzinfo=tz)
end = start + timedelta(minutes=30)

event = calendar.events.create(
    "primary",
    summary="Weekly sync",
    start=start,
    end=end,
    time_zone="America/New_York",
    recurrence=["RRULE:FREQ=WEEKLY;BYDAY=MO;COUNT=8"],
    send_updates=SendUpdates.NONE,
)
```

### All-day block

```python
from datetime import date, timedelta

start = date(2026, 12, 24)
calendar.events.create(
    "primary",
    summary="Holiday",
    start=start,
    end=start + timedelta(days=2),  # Dec 24–25 inclusive → exclusive end Dec 26
)
```

### Find a free slot (sketch)

```python
from datetime import UTC, datetime, timedelta

window_start = datetime.now(UTC)
window_end = window_start + timedelta(days=1)
busy = calendar.freebusy.query_one("primary", window_start, window_end)
# Compare candidate [slot_start, slot_end) against busy intervals
```

### Secondary calendar workflow

```python
cal = calendar.calendars.create("On-call", time_zone="UTC")
calendar.events.create(
    cal.id,
    summary="Pager shift",
    start=start,
    end=end,
    send_updates=SendUpdates.NONE,
)
calendar.calendars.update(cal.id, summary="On-call (legacy)")
# calendar.calendars.delete(cal.id)  # when finished
```

---

## Pitfalls

- **Naive datetimes**: rejected unless `ClientConfig.default_timezone` is set. Prefer explicit `tzinfo`.
- **All-day end exclusive**: one day ⇒ `end = start + 1 day`. Equal start/end raises `ValidationError`.
- **`sync_token` ⇒ `showDeleted=True`**: forced by GoogleKit; deleted/cancelled events appear in the feed. Do not pass conflicting time filters with sync tokens (they are dropped).
- **Expired sync tokens**: HTTP 410 — discard token and full-sync again.
- **`order_by="startTime"`**: only with `single_events=True` (default).
- **`SendUpdates` default `none`**: set `ALL` when you intentionally notify guests.
- **Meet**: `conference=True` requires write access; link is on `event.hangout_link` after create/update/patch.
- **`patch` + `response_status`**: pass `attendees` with one entry marked `self=True` (local flag only). GoogleKit sets `attendeesOmitted` on the event body and does **not** send read-only `self`/`organizer` fields.
- **Primary calendar**: cannot `calendars.delete("primary")`.
- **Windows timezones**: install `tzdata` for IANA `ZoneInfo` names.
- **Scopes**: events-only scopes are not enough for calendar list CRUD + freebusy; use the presets below.

---

## Scopes

`CalendarClient` exposes events, calendars, and freebusy. Presets authorize all three:

| Profile | Scopes |
| ------- | ------ |
| `metadata` | `calendar.readonly` |
| `readonly` | `calendar.events.readonly` + `calendar.calendarlist.readonly` + `calendar.calendars.readonly` + `calendar.freebusy` |
| `readwrite` (default) | `calendar.events` + `calendar.calendars` + `calendar.calendarlist` + `calendar.freebusy` |
| `full` | `calendar` (covers narrower calendar scopes) |

```python
from googlekit.auth.scopes import ScopeProfile
from googlekit.gcalendar import CalendarClient

calendar = CalendarClient.from_oauth(
    "client_secret.json",
    profile=ScopeProfile.READWRITE,
)
```

See also [scopes](scopes.md).
