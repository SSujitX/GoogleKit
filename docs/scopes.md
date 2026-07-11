# OAuth scopes

GoogleKit centralizes scopes in `googlekit.auth.scopes`.

## Principles

- Do not request all scopes by default
- Prefer least privilege via `ScopeProfile`
- Never silently escalate privileges
- `ScopeSet.covers()` / `missing()` treat full `drive` / `calendar` as covering narrower scopes

## Profiles

| Profile | Meaning |
| ------- | ------- |
| `metadata` | Minimal metadata / list-oriented access |
| `readonly` | Read without write |
| `readwrite` | Typical app create/edit (**default**) |
| `full` | Broadest service scope when truly required |

## Drive presets

| Profile | Scope(s) |
| ------- | -------- |
| `metadata` | `drive.metadata.readonly` |
| `readonly` | `drive.readonly` |
| `readwrite` | `drive.file` (files created/opened by the app) |
| `full` | `drive` |

Also available as constants: `drive.appdata`, `drive.appfolder`, `drive.apps.readonly`, `drive.meet.readonly`, `drive.install`, metadata variants.

## Sheets / Docs / Slides

| Service | readonly | readwrite / full |
| ------- | -------- | ---------------- |
| Sheets | `spreadsheets.readonly` | `spreadsheets` |
| Docs | `documents.readonly` | `documents` |
| Slides | `presentations.readonly` | `presentations` |

Export/share for Docs/Sheets/Slides also needs a Drive scope (usually `drive.file` or `drive`).

## Calendar presets

`CalendarClient` exposes **events**, **calendars**, and **freebusy**. Default presets authorize all three:

| Profile | Scopes |
| ------- | ------ |
| `metadata` | `calendar.readonly` |
| `readonly` | `calendar.events.readonly` + `calendar.calendarlist.readonly` + `calendar.calendars.readonly` + `calendar.freebusy` |
| `readwrite` | `calendar.events` + `calendar.calendars` + `calendar.calendarlist` + `calendar.freebusy` |
| `full` | `calendar` |

Additional constants exist for `calendar.events.freebusy`, `calendar.app.created`, `calendar.settings.readonly`, and more.

## Aggregation

```python
from googlekit.auth.scopes import ScopeProfile, aggregate_scopes, preset_for

scopes = aggregate_scopes(
    preset_for("gdrive", ScopeProfile.READWRITE),
    preset_for("gsheets", ScopeProfile.READONLY),
)
```

Unified client:

```python
from googlekit import GoogleKit
from googlekit.auth.scopes import ScopeProfile

client = GoogleKit.from_oauth(
    "client_secrets.json",
    services=["gdrive", "gsheets", "gcalendar"],
    profile=ScopeProfile.READWRITE,
)
```

## Insufficient scopes

Some cross-service helpers (Docs/Slides export and share via Drive) check scopes
locally and raise `InsufficientScopesError` with a reauthorize hint.

Most other API methods rely on Google to reject unauthorized calls (typically HTTP
403). Prefer requesting the correct [scope presets](#profiles) up front; OAuth tokens
are scope-bound, and installed apps do not support incremental authorization — expanding
scopes requires a fresh browser consent flow.

