---
title: GoogleKit — Python SDK for Google Workspace APIs
description: >-
  Unofficial Python SDK for Google Drive, Sheets, Calendar, Docs, and Slides APIs.
  OAuth 2.0, ADC, service accounts, typed clients, and retries in one package.
---

# GoogleKit

**Unofficial Python SDK** for the [Google Drive API](drive.md), [Google Sheets API](sheets.md), [Google Calendar API](calendar.md), [Google Docs API](docs.md), and [Google Slides API](slides.md).

!!! warning "Unofficial"
    GoogleKit is not affiliated with, endorsed by, or sponsored by Google.
    Google trademarks remain the property of their owners.
    Prefer the official product docs linked below when resolving API semantics.

**Site:** [https://ssujitx.github.io/GoogleKit/](https://ssujitx.github.io/GoogleKit/) · **PyPI:** [googlekit](https://pypi.org/project/googlekit/) · **Repo:** [SSujitX/GoogleKit](https://github.com/SSujitX/GoogleKit)

## Official Google documentation

| Product | Official docs |
| ------- | ------------- |
| Google Workspace APIs | [developers.google.com/workspace](https://developers.google.com/workspace) |
| Drive API | [Drive API guides](https://developers.google.com/workspace/drive/api/guides/about-sdk) · [REST reference](https://developers.google.com/workspace/drive/api/reference/rest/v3) |
| Sheets API | [Sheets API guides](https://developers.google.com/workspace/sheets/api/guides/concepts) · [REST reference](https://developers.google.com/workspace/sheets/api/reference/rest) |
| Calendar API | [Calendar API guides](https://developers.google.com/workspace/calendar/api/guides/overview) · [REST reference](https://developers.google.com/workspace/calendar/api/v3/reference) |
| Docs API | [Docs API guides](https://developers.google.com/workspace/docs/api/how-tos/overview) · [REST reference](https://developers.google.com/workspace/docs/api/reference/rest) |
| Slides API | [Slides API guides](https://developers.google.com/workspace/slides/api/guides/overview) · [REST reference](https://developers.google.com/workspace/slides/api/reference/rest) |
| OAuth 2.0 | [OAuth 2.0](https://developers.google.com/identity/protocols/oauth2) · [Scopes](https://developers.google.com/identity/protocols/oauth2/scopes) |
| ADC | [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials) |

## Why GoogleKit?

- One consistent Python API across five Google Workspace products
- **Managers** (full control) plus optional **shortcuts** (flat helpers) — both autocomplete after `client.drive.`
- Google client libraries included by default (`uv add googlekit` / `pip install googlekit`)
- OAuth 2.0 desktop, service accounts, and Application Default Credentials (ADC)
- Least-privilege scope presets per service
- Retries, lazy pagination, typed exceptions, and `py.typed` support

## Quick start

```python
from googlekit import GoogleKit
from googlekit.auth.scopes import ScopeProfile

client = GoogleKit.auto(services=["gdrive", "gsheets"], profile=ScopeProfile.FULL)

# Managers
page = client.drive.files.list(folder_id="root")
client.sheets.values.write("sid", "Sheet1!A1", [["Ada", 98]])

# Optional shortcuts (equivalent)
page = client.drive.list_files(folder_id="root")
client.sheets.write_values("sid", "Sheet1!A1", [["Ada", 98]])
```

Each service page documents **both** styles: [Drive](drive.md) · [Sheets](sheets.md) · [Calendar](calendar.md) · [Docs](docs.md) · [Slides](slides.md).

## Documentation map

### Getting started

| Page | What it covers |
| ---- | -------------- |
| [Installation](installation.md) | `pip` / `uv`, Python versions |
| [Authentication](authentication.md) | Four methods: ADC, service account, OAuth, auto-detect; security |
| [Scopes](scopes.md) | Scope presets, aggregation, `InsufficientScopesError` |
| [Errors](errors.md) | Exception hierarchy and HTTP mapping |

### Google Workspace services (full reference)

| Service | Page | Contents |
| ------- | ---- | -------- |
| Google Drive | [Drive](drive.md) | Managers + shortcuts, files, folders, permissions, Shared Drives |
| Google Sheets | [Sheets](sheets.md) | Managers + shortcuts, values, worksheets, formatting |
| Google Calendar | [Calendar](calendar.md) | Managers + shortcuts, events, Meet, free/busy |
| Google Docs | [Docs](docs.md) | Managers + shortcuts, text, tables, UTF-16 indexes |
| Google Slides | [Slides](slides.md) | Managers + shortcuts, pages, shapes, images, tables |

## Install

```bash
uv add googlekit
# or
pip install googlekit
```

Then enable the APIs you need in [Google Cloud Console → APIs & Services → Library](https://console.cloud.google.com/apis/library).
