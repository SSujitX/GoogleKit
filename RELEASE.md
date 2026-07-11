## [0.0.1] - 2026-07-12

First public release of **GoogleKit** — an unofficial Python SDK for Google Drive, Sheets, Calendar, Docs, and Slides.

### Added

- Core runtime: typed exceptions, retries, pagination, HTTP transport, client-library checks
- Authentication: OAuth 2.0 desktop flow, service accounts, Application Default Credentials (ADC), auto-detect
- Scope presets (`metadata` / `readonly` / `readwrite` / `full`) and `ScopeSet` aggregation
- Atomic token file writes with restrictive permissions when the OS supports them
- Unified `GoogleKit` client with lazy `drive` / `sheets` / `calendar` / `docs` / `slides` accessors
- Per-service clients: `DriveClient`, `SheetsClient`, `CalendarClient`, `DocsClient`, `SlidesClient`
- **Drive** — files, folders, permissions, changes, upload/download, native export, Shared Drives
- **Sheets** — spreadsheets, values (A1), worksheets, formatting helpers
- **Calendar** — calendars, events, Meet links, free/busy, sync tokens, attendee RSVP (`response_status`)
- **Docs** — documents, content/tables, UTF-16-safe indexes, tab-aware get (`includeTabsContent`)
- **Slides** — presentations, pages, shapes, images, tables, template text replace
- Configurable HTTP timeout and custom User-Agent on authorized requests
- Retries for transport failures and rate limits (including selected 403 rate-limit reasons)
- Minimal CLI: `googlekit --version`, `doctor`, `auth status`
- Docs site (MkDocs), examples, unit tests, CI, and PyPI publish workflow

### Notes

- Install: `pip install googlekit` or `uv add googlekit` (Google API client libraries included by default)
- Unified constructors require explicit `services=` or `scopes=` (no all-Workspace default)
- Not affiliated with Google LLC
