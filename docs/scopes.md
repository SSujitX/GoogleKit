# OAuth scopes

GoogleKit centralizes scopes in `googlekit.auth.scopes`.

## Principles

- Do not request all scopes by default
- Prefer least privilege via `ScopeProfile`
- Never silently escalate privileges
- Drive scopes distinguish app files, metadata, read-only, and full access

## Profiles

| Profile | Meaning |
| ------- | ------- |
| `metadata` | Minimal metadata / list-oriented access |
| `readonly` | Read without write |
| `readwrite` | Typical app create/edit (default) |
| `full` | Broadest service scope when truly required |

## Drive presets

| Profile | Scope |
| ------- | ----- |
| `metadata` | `drive.metadata.readonly` |
| `readonly` | `drive.readonly` |
| `readwrite` | `drive.file` (files created/opened by the app) |
| `full` | `drive` |

## Sheets / Docs / Slides

| Service | readonly | readwrite / full |
| ------- | -------- | ---------------- |
| Sheets | `spreadsheets.readonly` | `spreadsheets` |
| Docs | `documents.readonly` | `documents` |
| Slides | `presentations.readonly` | `presentations` |

## Calendar

| Profile | Scope |
| ------- | ----- |
| `metadata` | `calendar.readonly` |
| `readonly` | `calendar.events.readonly` |
| `readwrite` | `calendar.events` |
| `full` | `calendar` |

## Aggregation

```python
from googlekit.auth.scopes import ScopeProfile, aggregate_scopes, preset_for

scopes = aggregate_scopes(
    preset_for("gdrive", ScopeProfile.READWRITE),
    preset_for("gsheets", ScopeProfile.READONLY),
)
```

Unified client helpers:

```python
GoogleKit.from_oauth(..., services=["gdrive", "gsheets"], profile=ScopeProfile.READWRITE)
```

## Insufficient scopes

When a method needs a scope not granted, GoogleKit raises `InsufficientScopesError`
with the required scope(s) and a reauthorize hint. OAuth tokens are scope-bound;
adding a service after the first authorization typically requires a new consent flow.
