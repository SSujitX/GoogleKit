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
  <a href="https://github.com/SSujitX/GoogleKit/issues">Issues</a> •
  <a href="https://github.com/SSujitX/GoogleKit/blob/master/docs/index.md">Docs</a>
</p>

# GoogleKit

**GoogleKit is an unofficial Python SDK that wraps `google-api-python-client` for Google Drive, Sheets, Calendar, Docs, and Slides.**

> GoogleKit is **not** affiliated with, endorsed by, or sponsored by Google LLC.

A modern, typed library for Google Workspace APIs. Inspired by [PyDrive](https://pypi.python.org/pypi/PyDrive), [PyDrive2](https://github.com/iterative/PyDrive2), and [PyDrive4](https://github.com/SSujitX/pydrive4) — expanded beyond Drive into a consistent multi-service kit with simplified authentication and a clean manager-style API.

## Table of Contents

- [Features](#features)
- [Supported Services](#supported-services)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Authentication Methods](#authentication-methods)
  - [Method 1: Application Default Credentials](#method-1-application-default-credentials-recommended)
  - [Method 2: Service Account](#method-2-service-account-for-automation)
  - [Method 3: OAuth2 Client](#method-3-oauth2-client-credentials-recommended-for-personal-use)
  - [Auto-Detection Priority](#auto-detection-priority)
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

- **Multiple Auth Methods** — ADC, OAuth2 desktop, service account, plus `GoogleKit.auto()` detection
- **Five Workspace Services** — Drive, Sheets, Calendar, Docs, and Slides behind one package
- **Unified or Per-Service Clients** — `GoogleKit` or `DriveClient` / `SheetsClient` / …
- **Least-Privilege Scopes** — presets: `metadata`, `readonly`, `readwrite`, `full`
- **Drive File & Folder Ops** — upload, download, search, nested paths, recursive folder sync
- **Sharing Helpers** — user, group, domain, and explicit public link sharing
- **Sheets Values API** — read / write / append / clear with A1 ranges
- **Calendar Events** — create, list, Meet links, timezone-aware datetimes
- **Docs & Slides** — create, batch update, export via Drive, UTF-16-safe Docs indexes
- **Retries & Pagination** — resilient transport with lazy page iterators
- **Typed Public API** — `py.typed` package, actionable exceptions

## Supported Services

| Service | Module | Client |
| ------- | ------ | ------ |
| Google Drive | `googlekit.gdrive` | `DriveClient` |
| Google Sheets | `googlekit.gsheets` | `SheetsClient` |
| Google Calendar | `googlekit.gcalendar` | `CalendarClient` |
| Google Docs | `googlekit.gdocs` | `DocsClient` |
| Google Slides | `googlekit.gslides` | `SlidesClient` |

Enable the APIs you need in [Google Cloud Console](https://console.cloud.google.com/apis/library).

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

### Unified client

```python
from googlekit import GoogleKit

# Auto-authenticate (ADC → local JSON credentials)
kit = GoogleKit.auto(services=["gdrive", "gsheets"])

page = kit.drive.files.list(folder_id="root")
for f in page.items:
    print(f.name)

kit.sheets.values.write(
    "spreadsheet_id",
    "Sheet1!A1",
    [["Name", "Score"], ["Ada", 98]],
)
```

### Drive-only client

```python
from googlekit.gdrive import DriveClient

drive = DriveClient.from_oauth("client_secrets.json")
drive.files.upload_path("report.pdf")
```

---

## Authentication Methods

GoogleKit supports multiple authentication methods, ordered by recommendation for most workflows:

| Method | Factory | Best For | Setup Required |
| ------ | ------- | -------- | -------------- |
| **1. Application Default Credentials** | `from_adc()` / `auto()` | Local dev, Google Cloud | `gcloud` CLI |
| **2. Service Account** | `from_service_account()` | Servers, automation, bots | JSON key file |
| **3. OAuth2 Client** | `from_oauth()` | Personal scripts, desktop apps | JSON + browser auth |

**Security:** never commit `client_secrets.json`, service-account keys, or token files. OAuth tokens default to an OS user config directory when `token_path` is omitted.

---

### Method 1: Application Default Credentials (Recommended)

The **easiest** method for local development. No JSON files to manage!

#### Setup (One-time)

1. Install [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)

2. Login with your Google account:

```bash
gcloud auth application-default login
```

3. Use GoogleKit:

```python
from googlekit import GoogleKit

kit = GoogleKit.from_adc(services=["gdrive"])
# or
kit = GoogleKit.auto(services=["gdrive"])
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

Enable the APIs you need (Drive, Sheets, Calendar, Docs, and/or Slides) in
**APIs & Services → Library**.

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

# Explicit
kit = GoogleKit.from_service_account(
    "service_account.json",
    services=["gdrive", "gsheets"],
)

# Auto-detect (if service_account.json is in the working directory)
kit = GoogleKit.auto(services=["gdrive"])
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

**Step 1–2:** Create a Cloud project and enable the APIs you need.

**Step 3: OAuth Consent Screen**

1. **APIs & Services → OAuth consent screen**
2. Choose **External** (or Internal for Workspace)
3. Fill app name, support email, developer contact
4. Add yourself as a **Test user** while the app is in testing

**Step 4: Create OAuth Client ID**

1. **Credentials → Create Credentials → OAuth client ID**
2. Application type: **Desktop app**
3. Download JSON → rename to `client_secrets.json`

#### Usage

```python
from googlekit import GoogleKit

kit = GoogleKit.from_oauth(
    "client_secrets.json",
    token_path="token.json",  # optional; defaults to OS config dir
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

### Environment Variable

```bash
# Linux/macOS
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

# Windows PowerShell
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\credentials.json"
```

```python
kit = GoogleKit.from_adc(services=["gdrive"])
# or
kit = GoogleKit.auto(services=["gdrive"])
```

---

### Auto-Detection Priority

When you call `GoogleKit.auto()`, credential discovery tries:

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

---

## API Overview

### GoogleKit

```python
GoogleKit.from_oauth(client_secrets, token_path=None, *, services=None, profile=...)
GoogleKit.from_service_account(credentials_file, subject=None, *, services=None, profile=...)
GoogleKit.from_adc(*, services=None, profile=..., quota_project_id=None)
GoogleKit.auto(*, services=None, profile=...)
```

Lazy accessors: `kit.drive`, `kit.sheets`, `kit.calendar`, `kit.docs`, `kit.slides`.

### Drive (`kit.drive`)

| Manager | Highlights |
| ------- | ---------- |
| `files` | `list`, `iterate`, `search`, `get`, `upload_path`, `download_path`, `export`, `copy`, `move`, `rename`, `trash`, `restore`, `delete`, `empty_trash` |
| `folders` | `create`, `create_path`, `list_children`, `upload_directory`, `download_directory` |
| `permissions` | `share_user`, `share_group`, `share_domain`, `share_anyone` (needs `public=True`), `create_shareable_link`, `list`, `remove` |
| `changes` | `get_start_page_token`, `list`, `iterate` |

### Sheets (`kit.sheets`)

| Manager | Highlights |
| ------- | ---------- |
| `values` | `read`, `read_multiple`, `write`, `write_multiple`, `append`, `clear` |
| `spreadsheets` / `worksheets` | create, get, add/delete/duplicate sheets |
| `formatting` | text, number formats, borders, merge |

### Calendar (`kit.calendar`)

| Manager | Highlights |
| ------- | ---------- |
| `events` | `list`, `create`, `update`, `patch`, `delete` (Meet via `conference=True`) |
| `calendars` | calendar list / CRUD |
| `freebusy` | availability queries |

### Docs / Slides

| Client | Highlights |
| ------ | ---------- |
| `kit.docs` | `documents.create` / `get`, content helpers, tables, `export` / `share` via Drive |
| `kit.slides` | `presentations.create` / `get`, pages, elements, tables, images, text replace |

---

## Usage Examples

### Drive — list, upload, download

```python
from googlekit import GoogleKit

kit = GoogleKit.auto(services=["gdrive"])
drive = kit.drive

page = drive.files.list(folder_id="root")
for f in page.items:
    print(f"{f.name} ({f.id})")

uploaded = drive.files.upload_path("document.pdf", parents=["folder_id"])
drive.files.download_path(uploaded.id, "local-copy.pdf")
```

### Drive — folders and sharing

```python
folder = drive.folders.create_path("Projects/2026")
drive.folders.upload_directory("./my_project", parent_id=folder.id)

drive.permissions.share_user(folder.id, "colleague@example.com", role="writer")
link = drive.permissions.create_shareable_link(folder.id, public=True)
print(link)
```

### Sheets

```python
kit = GoogleKit.auto(services=["gsheets"])

kit.sheets.values.write(
    "spreadsheet_id",
    "Sheet1!A1:B2",
    [["Name", "Score"], ["Ada", 98]],
)
rows = kit.sheets.values.read("spreadsheet_id", "Sheet1!A1:B10")
print(rows)
```

### Calendar

```python
from datetime import UTC, datetime, timedelta

kit = GoogleKit.auto(services=["gcalendar"])
start = datetime.now(UTC)
end = start + timedelta(hours=1)

event = kit.calendar.events.create(
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
kit = GoogleKit.auto(services=["gdocs", "gslides", "gdrive"])

doc = kit.docs.documents.create("Proposal")
kit.docs.content.insert_text(doc.id, "Hello from GoogleKit\n", index=1)

deck = kit.slides.presentations.create("Pitch Deck")
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

kit = GoogleKit.from_oauth(
    "client_secrets.json",
    services=["gdrive"],
    profile=ScopeProfile.READONLY,
)
```

Missing scopes raise `InsufficientScopesError` with a clear reauth hint.
Calendar `readwrite` includes events, calendars, calendarList, and freebusy so the full `CalendarClient` surface works under the default preset.

---

## Error Handling

GoogleKit raises typed exceptions (it does **not** return `{"success": false}` dicts):

```python
from googlekit import GoogleKit
from googlekit.core.exceptions import GoogleKitError, NotFoundError, ValidationError

kit = GoogleKit.auto(services=["gdrive"])

try:
    kit.drive.files.get("missing-id")
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

This is an independent open-source project. Google and Google Workspace are trademarks of Google LLC.
GoogleKit is not affiliated with, endorsed by, or sponsored by Google.

---

## Acknowledgments

Auth auto-detection patterns inspired by [PyDrive4](https://github.com/SSujitX/pydrive4).
Earlier Drive wrappers: [PyDrive](https://pypi.python.org/pypi/PyDrive), [PyDrive2](https://github.com/iterative/PyDrive2).

<p align="center">
  <a href="https://www.star-history.com/#SSujitX/GoogleKit&Date">
    <img src="https://api.star-history.com/svg?repos=SSujitX/GoogleKit&type=Date" width="500" alt="Star History">
  </a>
</p>

<p align="center">
  <a href="https://visitorbadge.io/status?path=https%3A%2F%2Fgithub.com%2FSSujitX%2FGoogleKit"><img src="https://api.visitorbadge.io/api/visitors?path=https%3A%2F%2Fgithub.com%2FSSujitX%2FGoogleKit&countColor=%23263759" /></a>
</p>
