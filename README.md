<p align="center">
  <a href="https://pypi.org/project/googlekit/"><img src="https://img.shields.io/pypi/v/googlekit.svg" alt="PyPI version"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python"></a>
  <a href="https://pepy.tech/project/googlekit"><img src="https://static.pepy.tech/badge/googlekit" alt="Downloads"></a>
  <a href="https://pepy.tech/project/googlekit"><img src="https://static.pepy.tech/badge/googlekit/month" alt="Monthly Downloads"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
</p>

<p align="center">
  <a href="https://github.com/SSujitX/GoogleKit">GitHub</a> •
  <a href="https://pypi.org/project/googlekit/">PyPI</a> •
  <a href="https://ssujitx.github.io/GoogleKit/">Documentation</a> •
  <a href="https://github.com/SSujitX/GoogleKit/issues">Issues</a>
</p>

# GoogleKit

**GoogleKit is an unofficial Python SDK for the Google Drive API, Google Sheets API, Google Calendar API, Google Docs API, and Google Slides API.**

> GoogleKit is **not** affiliated with, endorsed by, or sponsored by Google LLC.

Use GoogleKit to upload and download Google Drive files, read and write Google Sheets spreadsheets, manage Google Calendar events, create Google Docs documents, and build Google Slides presentations — from one Python package. It wraps `google-api-python-client` with OAuth 2.0, service account, and Application Default Credentials (ADC) auth, least-privilege scopes, retries, and a clean typed API for Google Workspace automation, bots, scripts, and backend services.

Whether you need a Python Google Drive client, a Google Sheets Python library, a Google Calendar SDK, a Google Docs API wrapper, or a Google Slides API client, GoogleKit gives you one consistent Google Workspace Python SDK instead of wiring each Google API by hand.

## Table of Contents

- [Features](#features)
- [Supported Services](#supported-services)
- [Documentation](#documentation)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Authentication Methods](#authentication-methods)
  - [Method 1: Application Default Credentials](#method-1-application-default-credentials-recommended)
  - [Method 2: Service Account](#method-2-service-account-for-automation)
  - [Method 3: OAuth2 Client](#method-3-oauth2-client-credentials-recommended-for-personal-use)
  - [Method 4: Auto-detect](#method-4-auto-detect-auto)
  - [Environment Variable](#environment-variable)
- [API Overview](#api-overview)
- [Usage Examples](#usage-examples)
- [OAuth Scopes](#oauth-scopes)
- [Error Handling](#error-handling)
- [CLI](#cli)
- [Requirements](#requirements)
- [Development](#development)
- [License](#license)
- [Disclaimer](#disclaimer)

## Features

- **Google Drive API v3 (Python)** — upload, download, search, copy, move, trash, export Docs/Sheets/Slides, shared drives
- **Google Sheets API v4** — read, write, append, and clear cell values with A1 notation; formatting and worksheets
- **Google Calendar API v3** — create and list events, Google Meet conference links, free/busy, calendars
- **Google Docs API v1** — create documents, insert text, tables, batch updates, UTF-16-safe indexes
- **Google Slides API v1** — create presentations, pages, shapes, images, tables, template text replace
- **Google OAuth 2.0 & service accounts** — desktop OAuth, ADC (`gcloud auth application-default login`), JSON keys
- **Four auth factories** — `from_adc()`, `from_service_account()`, `from_oauth()`, and dedicated `auto()` discovery
- **Least-privilege OAuth scopes** — `readonly`, `readwrite`, `full` presets per Google API
- **Unified Google Workspace client** — one `GoogleKit` entry point or per-service clients (`DriveClient`, `SheetsClient`, …)
- **Production-ready transport** — retries, rate-limit handling, lazy pagination, typed exceptions
- **MIT open source** — install with `pip install googlekit` or `uv add googlekit`

## Supported Services

| Google API | Python module | Client class | Common tasks |
| ---------- | ------------- | ------------ | ------------ |
| Google Drive API | `googlekit.gdrive` | `DriveClient` | File upload/download, folders, sharing, export |
| Google Sheets API | `googlekit.gsheets` | `SheetsClient` | Spreadsheet values, worksheets, formatting |
| Google Calendar API | `googlekit.gcalendar` | `CalendarClient` | Events, Meet links, free/busy |
| Google Docs API | `googlekit.gdocs` | `DocsClient` | Documents, text, tables, export |
| Google Slides API | `googlekit.gslides` | `SlidesClient` | Presentations, slides, images, templates |

Enable each API in [Google Cloud Console → APIs & Services → Library](https://console.cloud.google.com/apis/library).

## Documentation

**Full docs:** [https://ssujitx.github.io/GoogleKit/](https://ssujitx.github.io/GoogleKit/)

| Topic | Link |
| ----- | ---- |
| Installation | [Docs → Installation](https://ssujitx.github.io/GoogleKit/installation/) |
| Authentication (OAuth, ADC, service account) | [Docs → Authentication](https://ssujitx.github.io/GoogleKit/authentication/) |
| OAuth scopes | [Docs → Scopes](https://ssujitx.github.io/GoogleKit/scopes/) |
| Errors | [Docs → Errors](https://ssujitx.github.io/GoogleKit/errors/) |
| **Google Drive API** — files, folders, sharing, changes, export | [Docs → Drive](https://ssujitx.github.io/GoogleKit/drive/) |
| **Google Sheets API** — values, worksheets, formatting | [Docs → Sheets](https://ssujitx.github.io/GoogleKit/sheets/) |
| **Google Calendar API** — events, Meet, free/busy, sync | [Docs → Calendar](https://ssujitx.github.io/GoogleKit/calendar/) |
| **Google Docs API** — text, tables, UTF-16 indexes | [Docs → Docs](https://ssujitx.github.io/GoogleKit/docs/) |
| **Google Slides API** — pages, shapes, images, templates | [Docs → Slides](https://ssujitx.github.io/GoogleKit/slides/) |

The README covers install, auth, and quick examples. Method-level reference, recipes, and pitfalls live on the docs site.

### Official Google API documentation

| Product | Guides | Reference |
| ------- | ------ | --------- |
| Google Workspace | [Workspace APIs](https://developers.google.com/workspace) | — |
| Drive | [Guides](https://developers.google.com/workspace/drive/api/guides/about-sdk) | [REST v3](https://developers.google.com/workspace/drive/api/reference/rest/v3) |
| Sheets | [Guides](https://developers.google.com/workspace/sheets/api/guides/concepts) | [REST](https://developers.google.com/workspace/sheets/api/reference/rest) |
| Calendar | [Guides](https://developers.google.com/workspace/calendar/api/guides/overview) | [REST v3](https://developers.google.com/workspace/calendar/api/v3/reference) |
| Docs | [Guides](https://developers.google.com/workspace/docs/api/how-tos/overview) | [REST](https://developers.google.com/workspace/docs/api/reference/rest) |
| Slides | [Guides](https://developers.google.com/workspace/slides/api/guides/overview) | [REST](https://developers.google.com/workspace/slides/api/reference/rest) |
| OAuth / scopes | [OAuth 2.0](https://developers.google.com/identity/protocols/oauth2) | [Scopes](https://developers.google.com/identity/protocols/oauth2/scopes) |

## Installation

```bash
pip install googlekit
```

Or with UV (recommended):

```bash
uv add googlekit
```

Google API client libraries are included by default — no extras required.

---

## Quick Start

GoogleKit exposes **managers** (full API) and optional **shortcuts** (flat helpers). Both are suggested after `client.drive.` / `client.sheets.` / … with hover docs.

### Unified client

```python
from googlekit import GoogleKit
from googlekit.auth.scopes import ScopeProfile

client = GoogleKit.auto(
    services=["gdrive", "gsheets"],
    profile=ScopeProfile.FULL,  # list all My Drive (not only drive.file)
)

# Managers (full control)
page = client.drive.files.list(folder_id="root")
client.sheets.values.write("spreadsheet_id", "Sheet1!A1", [["Ada", 98]])

# Optional shortcuts (same behavior, flatter)
page = client.drive.list_files(folder_id="root")
client.sheets.write_values("spreadsheet_id", "Sheet1!A1", [["Ada", 98]])
```

### Shortcuts at a glance (all services)

| Service | Shortcut examples | Equivalent managers |
| ------- | ----------------- | ------------------- |
| Drive | `list_files`, `upload_file`, `share`, … | `files.list`, `files.upload_path`, `permissions.share_user`, … |
| Sheets | `read_values`, `write_values`, `create_spreadsheet` | `values.read` / `write`, `spreadsheets.create` |
| Calendar | `list_events`, `create_event`, `delete_event` | `events.list` / `create` / `delete` |
| Docs | `create_document`, `append_text`, `insert_text` | `documents.create`, `content.append_text` / `insert_text` |
| Slides | `create_presentation`, `get_presentation`, `add_slide` | `presentations.create` / `get`, `pages.add` |

### Drive shortcuts (PyDrive4-style)

```python
from googlekit.gdrive import DriveClient
from googlekit.auth.scopes import ScopeProfile

drive = DriveClient.from_oauth(
    "client_secrets.json",
    profile=ScopeProfile.FULL,
)

# Shortcut                          # Manager equivalent
page = drive.list_files()           # drive.files.list(folder_id="root")
folders = drive.list_folders()      # drive.files.list(..., query=folder mime)
hits = drive.search_files("report") # drive.files.search("name contains 'report'")
folder = drive.create_folder("Reports")  # drive.folders.create(...)
result = drive.upload_file("report.pdf", folder_id=folder.id)
#                                     drive.files.upload_path(..., parents=[...])
drive.download_file(result.file.id, "report.pdf")
drive.share(result.file.id, email="you@example.com", role="reader")
# public link (explicit): drive.get_share_link(file_id, public=True)
```

### Other services — shortcut vs manager

```python
from datetime import UTC, datetime, timedelta
from googlekit import GoogleKit

client = GoogleKit.auto(services=["gsheets", "gcalendar", "gdocs", "gslides"])

# Sheets
client.sheets.write_values("sid", "Sheet1!A1", [["A", 1]])
client.sheets.values.write("sid", "Sheet1!A1", [["A", 1]])

# Calendar
start, end = datetime.now(UTC), datetime.now(UTC) + timedelta(hours=1)
client.calendar.create_event("primary", summary="Standup", start=start, end=end)
client.calendar.events.create("primary", summary="Standup", start=start, end=end)

# Docs
doc = client.docs.create_document("Proposal")
doc = client.docs.documents.create("Proposal")
client.docs.append_text(doc.id, "Hello\n")
client.docs.content.append_text(doc.id, "Hello\n")

# Slides
deck = client.slides.create_presentation("Pitch")
deck = client.slides.presentations.create("Pitch")
client.slides.add_slide(deck.id)
client.slides.pages.add(deck.id)
```

### Drive-only client (managers)

```python
from googlekit.gdrive import DriveClient

drive = DriveClient.from_oauth("client_secrets.json")
drive.files.upload_path("report.pdf")
```

---

## Authentication Methods

GoogleKit supports four authentication methods, ordered by recommendation for most workflows:

| Method | Factory | Best For | Setup Required |
| ------ | ------- | -------- | -------------- |
| **1. Application Default Credentials** | `from_adc()` | Local dev, Google Cloud | `gcloud` CLI |
| **2. Service Account** | `from_service_account()` | Servers, automation, bots | JSON key file |
| **3. OAuth2 Client** | `from_oauth()` | Personal scripts, desktop apps | JSON + browser auth |
| **4. Auto-detect** | `auto()` | Quick start / scripts that accept any local creds | ADC **or** a JSON file in CWD |

**Security:** never commit `client_secrets.json`, service-account keys, or token files. OAuth tokens default to `./token.json` in the current working directory when `token_path` is omitted (keep it gitignored).

---

### Method 1: Application Default Credentials (Recommended)

The **easiest** method for local development. No JSON files to manage!

#### Step-by-Step Setup

**Step 1: Create a Google Cloud Project**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Project dropdown → **New Project** → create and select it

**Step 2: Enable APIs**

Enable the APIs you need in
[APIs & Services → Library](https://console.cloud.google.com/apis/library):

| API | Enable |
| --- | ------ |
| Google Drive | [Enable Drive API](https://console.cloud.google.com/apis/library/drive.googleapis.com) |
| Google Sheets | [Enable Sheets API](https://console.cloud.google.com/apis/library/sheets.googleapis.com) |
| Google Calendar | [Enable Calendar API](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com) |
| Google Docs | [Enable Docs API](https://console.cloud.google.com/apis/library/docs.googleapis.com) |
| Google Slides | [Enable Slides API](https://console.cloud.google.com/apis/library/slides.googleapis.com) |

**Step 3: Install Google Cloud SDK and sign in**

1. Install [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
2. Login with your Google account:

```bash
gcloud auth application-default login
```

**Step 4: Use GoogleKit**

```python
from googlekit import GoogleKit

client = GoogleKit.from_adc(services=["gdrive"])
```

#### How it Works

ADC checks these locations in order:

1. `GOOGLE_APPLICATION_CREDENTIALS` environment variable
2. `gcloud auth application-default login` credentials
3. Google Cloud metadata service (on GCE, Cloud Run, etc.)

---

### Method 2: Service Account (For Automation)

Best for servers, bots, and CI/CD. **No browser interaction.**

#### Step-by-Step Setup

**Step 1: Create a Google Cloud Project**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Project dropdown → **New Project** → create and select it

**Step 2: Enable APIs**

Enable the APIs you need in
[APIs & Services → Library](https://console.cloud.google.com/apis/library):

| API | Enable |
| --- | ------ |
| Google Drive | [Enable Drive API](https://console.cloud.google.com/apis/library/drive.googleapis.com) |
| Google Sheets | [Enable Sheets API](https://console.cloud.google.com/apis/library/sheets.googleapis.com) |
| Google Calendar | [Enable Calendar API](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com) |
| Google Docs | [Enable Docs API](https://console.cloud.google.com/apis/library/docs.googleapis.com) |
| Google Slides | [Enable Slides API](https://console.cloud.google.com/apis/library/slides.googleapis.com) |

**Step 3: Create Service Account + JSON Key**

1. **IAM & Admin → Service Accounts → Create**
2. **Keys → Add Key → Create new key → JSON**
3. Rename the download to `service_account.json` and keep it out of git

#### Organization Policy Error

If key creation is blocked (`iam.disableServiceAccountKeyCreation`):

1. Use **OAuth2** (Method 3) or **ADC** (Method 1)
2. Or ask your admin for an exception

#### Usage

```python
from googlekit import GoogleKit

client = GoogleKit.from_service_account(
    "service_account.json",
    services=["gdrive", "gsheets"],
)
```

| Aspect | OAuth2 | Service Account |
| ------ | ------ | --------------- |
| Browser needed | Yes (first time) | No |
| Whose data? | Your Google account | The service account identity |
| Best for | Personal scripts | Servers, automation |
| Access | Files you own / can open | Only resources shared with the SA email |

> **Important:** Service accounts start with an empty Drive. Share folders/files with the SA email (e.g. `my-bot@my-project.iam.gserviceaccount.com`), or use domain-wide delegation with a `subject`.

---

### Method 3: OAuth2 Client Credentials (Recommended for Personal Use)

For desktop apps that access **your** Google account. Opens a browser once.

#### Step-by-Step Setup

**Step 1: Create a Google Cloud Project**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Project dropdown → **New Project** → create and select it

**Step 2: Enable APIs**

Enable the APIs you need in
[APIs & Services → Library](https://console.cloud.google.com/apis/library):

| API | Enable |
| --- | ------ |
| Google Drive | [Enable Drive API](https://console.cloud.google.com/apis/library/drive.googleapis.com) |
| Google Sheets | [Enable Sheets API](https://console.cloud.google.com/apis/library/sheets.googleapis.com) |
| Google Calendar | [Enable Calendar API](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com) |
| Google Docs | [Enable Docs API](https://console.cloud.google.com/apis/library/docs.googleapis.com) |
| Google Slides | [Enable Slides API](https://console.cloud.google.com/apis/library/slides.googleapis.com) |

**Step 3: Configure Google Auth Platform (OAuth app)**

Google now uses **[Google Auth Platform](https://console.cloud.google.com/auth/overview)** (not only the old “OAuth consent screen” page). Complete these before creating a client:

1. **[Branding](https://console.cloud.google.com/auth/branding)** — app name, support email, developer contact
2. **[Audience](https://console.cloud.google.com/auth/audience)** — **External** (or Internal for Workspace); while testing, add yourself as a test user
3. **[Data Access](https://console.cloud.google.com/auth/scopes)** — add the Google Workspace scopes you need (or GoogleKit will request them at runtime; listing them here helps consent / verification)

If the console still shows the older UI: **APIs & Services → [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent)** does the same job.

**Step 4: Create OAuth client (Desktop)**

You’re on the right page when you see **Clients** and **+ Create client** (empty until you create one):

1. Open **[Google Auth Platform → Clients](https://console.cloud.google.com/auth/clients)**
2. **+ Create client**
3. Application type: **Desktop app**
4. Name it (e.g. `GoogleKit desktop`) → **Create**
5. Download the JSON → rename to `client_secrets.json` (keep it out of git)

Older path (still works on some projects): **APIs & Services → [Credentials](https://console.cloud.google.com/apis/credentials) → Create Credentials → OAuth client ID → Desktop app**.

#### Usage

```python
from googlekit import GoogleKit

client = GoogleKit.from_oauth(
    "client_secrets.json",
    token_path="token.json",  # optional; defaults to ./token.json
    services=["gdrive", "gsheets", "gcalendar"],
)
```

**First run:** a browser window opens for consent. Tokens are cached for later runs.

Per-service clients:

```python
from googlekit.gdrive import DriveClient

drive = DriveClient.from_oauth("client_secrets.json")
```

---

### Method 4: Auto-detect (`auto()`)

Convenience factory that picks credentials for you — use when you want one call that works with ADC **or** a local JSON file.

```python
from googlekit import GoogleKit

client = GoogleKit.auto(services=["gdrive"])
# Optional: token_path=... when discovery lands on OAuth
```

Discovery order:

1. **Application Default Credentials** (`gcloud` login or `GOOGLE_APPLICATION_CREDENTIALS`)
2. **Service account files** in the working directory:
   - `service_account.json`
   - `service_account_key.json`
   - `sa_credentials.json`
3. **OAuth client files** in the working directory:
   - `client_secrets.json`
   - `client_secret.json`
   - `credentials.json`
   - `oauth_credentials.json`
4. Raise `AuthenticationError` with setup guidance

Prefer explicit `from_adc()` / `from_service_account()` / `from_oauth()` in production when you know which credential type you need.

---

### Environment Variable

```bash
# Linux/macOS
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

# Windows PowerShell
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\credentials.json"
```

```python
client = GoogleKit.from_adc(services=["gdrive"])
# or Method 4: GoogleKit.auto(services=["gdrive"])
```

---

## API Overview

### GoogleKit

```python
GoogleKit.from_oauth(client_secrets, token_path=None, *, services=[...], profile=...)
GoogleKit.from_service_account(credentials_file, subject=None, *, services=[...], profile=...)
GoogleKit.from_adc(*, services=[...], profile=..., quota_project_id=None)
GoogleKit.auto(*, services=[...], profile=...)
```

`services` (or explicit `scopes=`) is **required** on unified constructors so GoogleKit never requests every Workspace write scope by default.

Lazy accessors: `client.drive`, `client.sheets`, `client.calendar`, `client.docs`, `client.slides`.

### Config and retries

```python
from googlekit import ClientConfig, RetryPolicy

ClientConfig(retry=5)  # shorthand → RetryPolicy(max_attempts=5)
ClientConfig(retry=RetryPolicy(max_attempts=8, initial_delay=1.0))
ClientConfig(timeout=60, default_timezone="UTC")
```

Pass `config=` into `GoogleKit.from_oauth` / `.auto` or any service `from_*` factory.

### Drive (`client.drive`)

| Manager | Highlights |
| ------- | ---------- |
| `files` | `list`, `iterate`, `search`, `get`, `upload_path`, `download_path`, `export`, `copy`, `move`, `rename`, `trash`, `restore`, `delete`, `empty_trash` |
| `folders` | `create`, `create_path`, `list_children`, `upload_directory`, `download_directory` |
| `permissions` | `share_user`, `share_group`, `share_domain`, `share_anyone` (needs `public=True`), `create_shareable_link`, `list`, `remove` |
| `changes` | `get_start_page_token`, `list`, `iterate` |

**Shortcuts:** `list_files`, `list_folders`, `search_files`, `search_folders`, `create_folder`, `upload_file`, `download_file`, `upload_folder`, `delete_file` / `delete_folder`, `share`, `unshare`, `list_permissions`, `get_share_link`

### Sheets (`client.sheets`)

| Manager | Highlights |
| ------- | ---------- |
| `values` | `read`, `read_multiple`, `write`, `write_multiple`, `append`, `clear` |
| `spreadsheets` / `worksheets` | create, get, add/delete/duplicate sheets |
| `formatting` | text, number formats, borders, merge |

**Shortcuts:** `create_spreadsheet`, `get_spreadsheet`, `read_values`, `write_values`, `append_values`

### Calendar (`client.calendar`)

| Manager | Highlights |
| ------- | ---------- |
| `events` | `list`, `create`, `update`, `patch`, `delete` (Meet via `conference=True`) |
| `calendars` | calendar list / CRUD |
| `freebusy` | availability queries |

**Shortcuts:** `list_events`, `create_event`, `get_event`, `delete_event`

### Docs / Slides

| Client | Highlights |
| ------ | ---------- |
| `client.docs` | `documents.create` / `get`, content helpers, tables, `export` / `share` via Drive |
| `client.slides` | `presentations.create` / `get`, pages, elements, tables, images, text replace |

**Docs shortcuts:** `create_document`, `get_document`, `append_text`, `insert_text`  
**Slides shortcuts:** `create_presentation`, `get_presentation`, `add_slide`

---

## Usage Examples

### Drive — list, upload, download

```python
from googlekit import GoogleKit
from googlekit.auth.scopes import ScopeProfile

client = GoogleKit.auto(services=["gdrive"], profile=ScopeProfile.FULL)
drive = client.drive

# Manager
page = drive.files.list(folder_id="root")
# Shortcut (equivalent)
page = drive.list_files(folder_id="root")

for f in page.items:
    print(f"{f.name} ({f.id})")

uploaded = drive.files.upload_path("document.pdf", parents=["folder_id"])
# or: drive.upload_file("document.pdf", folder_id="folder_id")
drive.files.download_path(uploaded.file.id, "local-copy.pdf")
# or: drive.download_file(uploaded.file.id, "local-copy.pdf")
```

### Drive — folders and sharing

```python
folder = drive.folders.create_path("Projects/2026")
# or: drive.create_folder("Projects") then nest as needed
drive.folders.upload_directory("./my_project", parent_id=folder.id)
# or: drive.upload_folder("./my_project", parent_id=folder.id)

drive.permissions.share_user(folder.id, "colleague@example.com", role="writer")
# or: drive.share(folder.id, email="colleague@example.com", role="writer")
link = drive.permissions.create_shareable_link(folder.id, public=True)
# or: drive.get_share_link(folder.id, public=True)
print(link)
```

### Sheets

```python
client = GoogleKit.auto(services=["gsheets"])

# Manager
client.sheets.values.write(
    "spreadsheet_id",
    "Sheet1!A1:B2",
    [["Name", "Score"], ["Ada", 98]],
)
rows = client.sheets.values.read("spreadsheet_id", "Sheet1!A1:B10")

# Shortcut (equivalent)
client.sheets.write_values(
    "spreadsheet_id",
    "Sheet1!A1:B2",
    [["Name", "Score"], ["Ada", 98]],
)
rows = client.sheets.read_values("spreadsheet_id", "Sheet1!A1:B10")
print(rows)
```

### Calendar

```python
from datetime import UTC, datetime, timedelta

client = GoogleKit.auto(services=["gcalendar"])
start = datetime.now(UTC)
end = start + timedelta(hours=1)

# Manager
event = client.calendar.events.create(
    "primary",
    summary="Standup",
    start=start,
    end=end,
    conference=True,
)
# Shortcut (equivalent)
event = client.calendar.create_event(
    "primary",
    summary="Standup",
    start=start,
    end=end,
    conference=True,
)
print(event.id)
```

### Docs & Slides

```python
client = GoogleKit.auto(services=["gdocs", "gslides", "gdrive"])

# Docs — manager / shortcut
doc = client.docs.documents.create("Proposal")
doc = client.docs.create_document("Proposal")
client.docs.content.insert_text(doc.id, "Hello from GoogleKit\n", index=1)
client.docs.insert_text(doc.id, "Hello from GoogleKit\n", index=1)

# Slides — manager / shortcut
deck = client.slides.presentations.create("Pitch Deck")
deck = client.slides.create_presentation("Pitch Deck")
client.slides.pages.add(deck.id)
client.slides.add_slide(deck.id)
print(deck.id)
```

---

## OAuth Scopes

GoogleKit uses **least-privilege** scope presets per service:

| Profile | Typical meaning |
| ------- | --------------- |
| `metadata` | Minimal metadata access |
| `readonly` | Read-only |
| `readwrite` | Default for most apps |
| `full` | Broadest service scope |

```python
from googlekit import GoogleKit
from googlekit.auth.scopes import ScopeProfile

client = GoogleKit.from_oauth(
    "client_secrets.json",
    services=["gdrive"],
    profile=ScopeProfile.READONLY,
)
```

Docs/Slides cross-service Drive helpers detect missing Drive scopes locally and
raise `InsufficientScopesError`. Most other calls rely on Google returning HTTP
403 when the credential lacks a required scope.
Calendar `readwrite` includes events, calendars, calendarList, and freebusy so the full `CalendarClient` surface works under the default preset.

---

## Error Handling

GoogleKit raises typed exceptions (it does **not** return `{"success": false}` dicts):

```python
from googlekit import GoogleKit
from googlekit.core.exceptions import GoogleKitError, NotFoundError, ValidationError

client = GoogleKit.auto(services=["gdrive"])

try:
    client.drive.files.get("missing-id")
except NotFoundError as exc:
    print(exc)
except ValidationError as exc:
    print(exc)
except GoogleKitError as exc:
    print(exc)
```

Common types: `AuthenticationError`, `InsufficientScopesError`, `NotFoundError`,
`RateLimitError`, `QuotaExceededError`, `ValidationError`, `APIError`.

---

## CLI

```bash
uv run googlekit --version
uv run googlekit doctor
uv run googlekit auth status
```

`doctor` checks Python, Google client libraries, detected credential files, and token cache paths — without printing secrets.

---

## Requirements

- Python 3.11+
- `google-api-python-client` >= 2.198.0
- `google-auth` >= 2.55.2
- `google-auth-oauthlib` >= 1.4.0
- `google-auth-httplib2` >= 0.4.0

---

## Development

```bash
git clone https://github.com/SSujitX/GoogleKit.git
cd GoogleKit
uv sync --group dev
uv run pytest -m "not integration"
uv build
```

See [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/](docs/).

---

## License

MIT License — see [LICENSE](LICENSE).

---

## Disclaimer

This is an independent open-source project. Google, Google Drive, Google Sheets, Google Calendar, Google Docs, Google Slides, and Google Workspace are trademarks of Google LLC.
GoogleKit is not affiliated with, endorsed by, or sponsored by Google.

<p align="center">
  <a href="https://www.star-history.com/#SSujitX/GoogleKit&Date">
    <img src="https://api.star-history.com/svg?repos=SSujitX/GoogleKit&type=Date" width="500" alt="Star History">
  </a>
</p>

<p align="center">
  <a href="https://visitorbadge.io/status?path=https%3A%2F%2Fgithub.com%2FSSujitX%2FGoogleKit"><img src="https://api.visitorbadge.io/api/visitors?path=https%3A%2F%2Fgithub.com%2FSSujitX%2FGoogleKit&countColor=%23263759" /></a>
</p>
