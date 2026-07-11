# GoogleKit — Agent / LLM Reference

> **Purpose:** This file is the source of truth for how GoogleKit works *today*.
> Any LLM or agent working in this repo should read it before changing code, docs, or releases.
> It describes the **implemented** package — not a greenfield build prompt.

**Package:** `googlekit` (PyPI) · **Import:** `googlekit` · **Layout:** `src/googlekit/`  
**Docs:** https://ssujitx.github.io/GoogleKit/ · **Repo:** https://github.com/SSujitX/GoogleKit  
**Disclaimer:** Unofficial SDK — not affiliated with Google LLC.

---

## 1. What GoogleKit is

Unofficial Python SDK wrapping Google’s discovery clients for:

| Service | Module | Client | Google API |
| ------- | ------ | ------ | ---------- |
| Drive | `googlekit.gdrive` | `DriveClient` | Drive API v3 |
| Sheets | `googlekit.gsheets` | `SheetsClient` | Sheets API v4 |
| Calendar | `googlekit.gcalendar` | `CalendarClient` | Calendar API v3 |
| Docs | `googlekit.gdocs` | `DocsClient` | Docs API v1 |
| Slides | `googlekit.gslides` | `SlidesClient` | Slides API v1 |

Two usage styles (both supported):

```python
from googlekit import GoogleKit
client = GoogleKit.from_oauth("client_secrets.json", services=["gdrive", "gsheets"])
client.drive.files.list(...)           # managers
client.drive.list_files(...)           # optional shortcuts (same + hover docs)

from googlekit.gdrive import DriveClient
drive = DriveClient.from_oauth("client_secrets.json")
```

Shortcuts are declared on `DriveAPI` / `SheetsAPI` / … so IDE autocomplete after `drive.` shows both managers and flat helpers.

---

## 2. Install & packaging (critical)

### Install

```bash
uv add googlekit
# or
pip install googlekit
```

Google client libraries are **default** dependencies. There are **no** service extras (`[drive]`, `[all]`, etc.).

### Runtime dependencies (`pyproject.toml`)

- `google-api-python-client>=2.198.0`
- `google-auth>=2.55.2`
- `google-auth-oauthlib>=1.4.0`
- `google-auth-httplib2>=0.4.0`
- Python `>=3.11` (CI: 3.11 and 3.14)

### Version

- Single source: `pyproject.toml` → `[project].version` (only place to bump)
- Runtime: `googlekit.__version__` and `USER_AGENT` read via `importlib.metadata` (`package_version()`)
- Fallback when not installed: `"dev"` — never hardcode a release version in source
- Publish tags must be `v` + that version (`v0.0.2` ↔ `0.0.2`)
- After bumping: `uv sync` (so local env metadata matches) then tag

### Build / tool

- Hatchling, `src` layout, `uv` for lock/sync/build/publish
- Dev group: pytest, pytest-cov, mkdocs, mkdocs-material\[imaging\]
- Wheel contains all five service packages; missing Google libs at runtime → `MissingExtraError` telling user to `uv add googlekit`

### Naming

- Variable name for the unified client: prefer `client`, never `kit`
- Service keys: `gdrive`, `gsheets`, `gcalendar`, `gdocs`, `gslides` (aliases `drive`/`sheets`/… accepted in places)

---

## 3. Repository map

```
src/googlekit/
  __init__.py          # GoogleKit + exceptions + __version__
  client.py            # Unified GoogleKit
  __main__.py          # CLI
  auth/                # OAuth, SA, ADC, scopes, token stores
  core/                # transport, retries, exceptions, config, pagination
  gdrive/              # Drive managers
  gsheets/             # Sheets managers
  gcalendar/           # Calendar managers
  gdocs/               # Docs managers + utf16 + Drive bridge
  gslides/             # Slides managers
docs/                  # MkDocs site
examples/              # Runnable samples
tests/unit|packaging|integration/
.github/workflows/     # ci.yml, docs.yml, publish.yml
RELEASE.md             # Notes for the current release section ## [X.Y.Z]
```

---

## 4. Authentication

### User-facing methods

| # | Method | Factory | Notes |
| - | ------ | ------- | ----- |
| 1 | ADC | `from_adc()` | Explicit ADC only |
| 2 | Service account | `from_service_account()` | JSON key; optional `subject` |
| 3 | OAuth desktop | `from_oauth()` | Browser consent; token cache |
| 4 | Auto-detect | `auto()` | ADC → SA file → OAuth file (not the same as `from_adc`) |

Do **not** document `auto()` as an alias of `from_adc()` — it is a separate discovery factory.

### Providers (`auth/`)

| Provider | File | When |
| -------- | ---- | ---- |
| `OAuthCredentialProvider` | `auth/oauth.py` | Desktop installed-app flow |
| `ServiceAccountCredentialProvider` | `auth/service_account.py` | JSON key; optional `subject` (DWD) |
| `ADCCredentialProvider` | `auth/adc.py` | `google.auth.default` / gcloud ADC |
| `build_provider` / `auto_detect_*` | `auth/credentials.py` | Wiring + file discovery |

### Unified factories (`client.py`)

```python
GoogleKit.from_oauth(client_secrets, token_path=None, *, services=..., profile=..., scopes=..., config=...)
GoogleKit.from_service_account(credentials_file, subject=None, *, services=..., ...)
GoogleKit.from_adc(*, services=..., quota_project_id=None, ...)
GoogleKit.auto(*, services=..., ...)   # ADC → SA file → OAuth file
```

**Hard rule:** unified constructors require `services=[...]` **or** explicit `scopes=`.  
They never default to “all Workspace write scopes.”

### Auto-detect order (`GoogleKit.auto` / `build_provider(method="auto")`)

1. Try ADC
2. CWD service-account files: `service_account.json`, `service_account_key.json`, `sa_credentials.json`
3. CWD OAuth files: `client_secrets.json`, `client_secret.json`, `credentials.json`, `oauth_credentials.json`, then `client_secret_*.json`
4. Else `AuthenticationError` with setup hints

### OAuth scope cache (do not regress)

Installed apps **cannot** incremental-authorize.

- Load cached token **without** injecting newly requested scopes into `Credentials.from_authorized_user_info`
- Accept cache only if granted scopes **cover** the request (`_token_covers_required`)
- Empty/missing granted scopes → treat as insufficient → browser reauth
- Expanding scopes beyond the token → full consent again

### Token store (`auth/token_store.py`)

- `FileTokenStore`: atomic write (`mkstemp` → write → `replace`)
- Mode `0600` via `fchmod` when available (POSIX); **skip `fchmod` on Windows** (`getattr(os, "fchmod", None)`); still try `chmod` after replace
- Default path: `./token.json` in the process current working directory
- Optional: `user_config_token_path()` → Windows `%APPDATA%/googlekit/token.json`; Unix XDG/`~/.config/googlekit/token.json`
- `GoogleKit.auto(..., token_path=...)` is supported; omit to use `./token.json` for OAuth
- Keep `token.json` gitignored (already in `.gitignore`)
- `InMemoryTokenStore` for tests

### Cloud Console (docs must stay current)

- Enable APIs: [APIs & Services → Library](https://console.cloud.google.com/apis/library)
- OAuth app: **Google Auth Platform** — Branding, Audience, Data Access, then **Clients → Desktop app**  
  ([Clients](https://console.cloud.google.com/auth/clients))
- Older path still exists: APIs & Services → Credentials / OAuth consent screen

---

## 5. Scopes (`auth/scopes.py`)

- `Scope`, `ScopeSet`, `ScopeProfile` (`metadata` | `readonly` | `readwrite` | `full`)
- `preset_for(service, profile)`, `aggregate_scopes(...)`
- `ScopeSet.covers` / `missing`: full `drive` / `calendar` cover narrower scopes

### Important presets

| Service | `readwrite` (default) meaning |
| ------- | ----------------------------- |
| Drive | `drive.file` (app-created/opened files) — **not** full `drive` |
| Sheets | `spreadsheets` |
| Docs | `documents` |
| Slides | `presentations` |
| Calendar | events + calendars + calendarlist + freebusy together |

Docs/Slides **export/share** need Drive scopes — GoogleKit **never** silently adds them. Local check → `InsufficientScopesError`.

---

## 6. Core runtime

### `ClientConfig` (`core/configuration.py`)

- `user_agent`, `timeout` (default 120s), `chunk_size` (256 KiB), `retry`, `supports_all_drives=True`, `default_timezone`
- `with_retries_disabled()` for tests

### Transport (`core/transport.py`)

- Builds/caches discovery services
- Sets httplib2 timeout from config
- **`_UserAgentHttp`**: wraps `AuthorizedHttp.request` and injects User-Agent every call  
  (assigning `http.headers["user-agent"]` alone is **not** reliable with AuthorizedHttp)
- `map_http_error`: 404→NotFound, 409/412→Conflict, 429→RateLimit, 403 rate-limit reasons→RateLimit, 403 quota→QuotaExceeded, else APIError
- Retries via `RetryPolicy` / `call_with_retries` (rate limit, transport, timeouts, selected 5xx)

### Exceptions (`core/exceptions.py`)

Hierarchy rooted at `GoogleKitError`. Public re-exports from `googlekit`.  
Never log tokens or Authorization headers.

### Pagination (`core/pagination.py`)

`Page[T]`, lazy `PageIterator[T]` with `.pages()`.

### Optional / extras labeling (`core/optional.py`)

`require_extra("gdrive")` etc. — labels only; install is monolithic.

---

## 7. Unified client wiring (`client.py`)

- Lazy properties: `.drive`, `.sheets`, `.calendar`, `.docs`, `.slides` (typed as `DriveAPI` / `SheetsAPI` / … so IDE autocomplete shows managers **and** shortcuts, not `from_oauth`)
- Shared `CredentialProvider` + `ClientConfig` across services
- `share_provider(client)` for Docs/Slides Drive bridge or custom multi-client setups
- `_primary_extra` picks first service for `require_extra` messaging

---

## 8. Drive (`gdrive/`)

**Managers:** `files`, `folders`, `permissions`, `changes` (lazy on `DriveClient`)

| Manager | Role |
| ------- | ---- |
| `FilesManager` + `FileMediaMixin` | list/search/CRUD/media upload/download/export |
| `FoldersManager` | create, `create_path` (reuse existing names), tree sync |
| `PermissionsManager` | share user/group/domain/anyone, roles, links |
| `ChangesManager` | start page token + incremental feed |

### Quirks (do not break)

- Shared Drives via `ClientConfig.supports_all_drives` / `shared_drive_params`
- `corpora="drive"` requires `drive_id` and vice versa
- `empty_trash` needs full `drive` scope
- Public share / shareable link requires explicit `public=True`
- Upload overwrite: `OverwritePolicy` ERROR | SKIP | OVERWRITE
- Google-native files need `export_format` to download; directory download exports natives as PDF
- Folder upload/download: reuse folders by name; PDF export collision checks `name.pdf`
- Symlink cycles skipped on upload; Drive shortcuts skipped on download

---

## 9. Sheets (`gsheets/`)

**Managers (eager):** `spreadsheets`, `values`, `worksheets`, `formatting`

- Values: A1 ranges; `read` / `write` / `append` / `clear` (+ batch variants)
- Worksheets: create/rename/delete/duplicate/reorder/resize/freeze/hide
- Formatting: text/number/background/alignment/borders + merge/sizes/conditional
- Grid ranges: 0-indexed, end exclusive
- `borders.width` accepted in API but **not sent** (deprecated field)

---

## 10. Calendar (`gcalendar/`)

**Managers:** `calendars`, `events`, `freebusy`

### Quirks (do not break)

- Timed events: timezone-aware `datetime` **or** `ClientConfig.default_timezone`
- All-day: `end.date` is **exclusive**
- `send_updates` defaults to `SendUpdates.NONE` (no guest emails unless asked)
- `conference=True` → Meet + `conferenceDataVersion=1`
- Sync token listing: forces `showDeleted=True`; drops incompatible filters
- **RSVP** `events.patch(..., response_status=..., attendees=[...])`:
  - Identify participant with `Attendee.self` / dict `self=True` **locally**
  - Do **not** send read-only `self` / `organizer` in the body (`Attendee.to_api` omits them)
  - Put `attendeesOmitted: true` on the **event body**, not as `patch()` query kwarg
  - Require at least one `self=True` attendee or raise `ValidationError`

---

## 11. Docs (`gdocs/`)

**Managers:** `documents`, `content`, `tables`, `images`

### Quirks (do not break)

- Indexes are **UTF-16 code units** (`gdocs/utf16.py`) — never assume Python `str` indexes
- `documents.get(..., include_tabs_content=True)` by default; parse `Document.tabs` / `DocumentTab`; prefer first tab body when legacy body empty
- Content ops accept `tab_id` for multi-tab docs
- `export` / `share` go through Drive (`_drive_bridge.py`) — need Drive scopes; never auto-add

---

## 12. Slides (`gslides/`)

**Managers:** `presentations`, `pages`, `elements`, `text`, `images`, `tables`

- Geometry in EMU (`pt_to_emu`, `inches_to_emu`)
- `export` / `share` same Drive-bridge rules as Docs
- Template helpers: `replace_all` / `replace_placeholders`

---

## 13. CLI (`__main__.py`)

```bash
googlekit --version
googlekit doctor      # python, libs, credential file detect, token path — no secrets
googlekit auth status
```

---

## 14. Testing

```bash
uv run pytest -m "not integration"
```

- `tests/unit/` — mocked / local (auth, core, each service)
- `tests/packaging/` — install/wheel contracts
- `tests/integration/` — live APIs; **excluded** in CI (`-m "not integration"`)
- Hard CI gates: pytest + wheel build/smoke only (no ruff/mypy as merge blockers)

When fixing Calendar RSVP or User-Agent, add/adjust unit tests that assert **outgoing** payload/headers (not only happy-path mocks).

---

## 15. Docs site & SEO

- MkDocs Material: `mkdocs.yml`, pages under `docs/`
- Per-page YAML `title` / `description` for meta
- Social cards: enabled in Docs workflow via `GOOGLEKIT_SOCIAL_CARDS=true` (needs Cairo; skipped locally on Windows by default)
- Link official Google Workspace docs from service pages
- Strict build: `uv run mkdocs build --strict`

---

## 16. Release & publish

Maintainer-only. See [`CONTRIBUTING.md`](CONTRIBUTING.md) (section **Maintainer: publishing to PyPI**) and [`RELEASE.md`](RELEASE.md).  
Not part of the public docs site.

Workflow: `.github/workflows/publish.yml` on tag `v*`

1. Unit tests  
2. Tag must match `pyproject.toml` version  
3. `uv build` + smoke import  
4. `uv publish` via **Trusted Publishing** (OIDC — no PyPI API token in secrets)  
5. GitHub Release body from `RELEASE.md` section `## [X.Y.Z]` + attach wheel/sdist  

`run-name: "PyPI publish ${{ github.ref_name }}"`

First-time PyPI: register a **pending** Trusted Publisher (`googlekit`, repo `SSujitX/GoogleKit`, workflow `publish.yml`, empty environment).

---

## 17. Agent rules (when editing this repo)

1. Prefer official Google API docs for semantics; GoogleKit is a thin typed wrapper.
2. Do not reintroduce service extras or all-scopes default on `GoogleKit`.
3. Do not “fix” OAuth by stuffing new scopes into cached credentials.
4. Do not send Calendar `attendees[].self` / `organizer` in write payloads.
5. Do not put `attendeesOmitted` on `events.patch` kwargs — only on event body.
6. Keep Docs indexes UTF-16-safe; keep tabs/`includeTabsContent` behavior.
7. Keep User-Agent injection via `_UserAgentHttp`, not only httplib2 `.headers`.
8. Keep token writes atomic and Windows-safe (`fchmod` optional).
9. Never commit secrets (`client_secrets.json`, tokens, SA keys).
10. Never add Cursor co-author trailers to commits unless the user asks.
11. Commits only when the user requests them.
12. Public share APIs stay behind `public=True`.
13. Docs/Slides export/share must not silently expand Drive scopes.
14. After behavior changes, update unit tests that assert request shape; update README/docs if user-facing.
15. Bump version in `pyproject.toml` + `RELEASE.md` together before tagging.

---

## 18. Quick “where is X?” index

| Concern | Path |
| ------- | ---- |
| Unified client | `src/googlekit/client.py` |
| OAuth + scope cache | `src/googlekit/auth/oauth.py` |
| Scope presets | `src/googlekit/auth/scopes.py` |
| Token atomic write | `src/googlekit/auth/token_store.py` |
| HTTP / UA / error map | `src/googlekit/core/transport.py` |
| Retries | `src/googlekit/core/retries.py` |
| Exceptions | `src/googlekit/core/exceptions.py` |
| Drive files/media | `src/googlekit/gdrive/files.py`, `file_media.py`, `transfers.py` |
| Drive folders | `src/googlekit/gdrive/folders.py` |
| Calendar RSVP | `src/googlekit/gcalendar/events.py`, `models.py` (`Attendee.to_api`) |
| Docs tabs / get | `src/googlekit/gdocs/documents.py`, `models.py` |
| Docs UTF-16 | `src/googlekit/gdocs/utf16.py` |
| Docs/Slides→Drive | `src/googlekit/gdocs/_drive_bridge.py` (Slides uses same pattern) |
| CLI | `src/googlekit/__main__.py` |
| Publish workflow | `.github/workflows/publish.yml` |

---

## 19. Minimal correct examples

```python
from googlekit import GoogleKit
from googlekit.auth.scopes import ScopeProfile

# Always pass services= (or scopes=)
client = GoogleKit.auto(services=["gdrive"], profile=ScopeProfile.FULL)

# Managers and optional shortcuts (both valid; both on DriveAPI for IDE)
page = client.drive.files.list(folder_id="root", page_size=50)
page = client.drive.list_files(folder_id="root", page_size=50)
for f in page.items:
    print(f.name, f.id)

# Sheets / Calendar / Docs / Slides — same dual style
client.sheets.values.write("sid", "A1", [["x"]])
client.sheets.write_values("sid", "A1", [["x"]])
client.calendar.create_event("primary", summary="X", start=..., end=...)
client.docs.create_document("Hello")          # or documents.create
client.slides.create_presentation("Deck")     # or presentations.create
```

```python
from googlekit.gcalendar.models import Attendee, SendUpdates

# RSVP: self is local-only
client.calendar.events.patch(
    "primary",
    event_id,
    attendees=[
        Attendee(email="me@example.com", self=True),
        Attendee(email="guest@example.com"),
    ],
    response_status="accepted",
    send_updates=SendUpdates.NONE,
)
```

```python
# Docs + Drive export needs both services/scopes
client = GoogleKit.from_oauth(
    "client_secrets.json",
    services=["gdocs", "gdrive"],
)
doc = client.docs.documents.create(title="Hello")
client.docs.documents.export(doc.document_id, mime_type="application/pdf", dest_path="out.pdf")
```

---

*End of agent reference. Prefer this file + source over outdated conversation summaries when they conflict.*
