## [0.0.3] - 2026-07-12

### Added

#### Optional convenience shortcuts (all services)

Flat helpers that delegate to managers — managers remain the full API:

- **Drive:** `list_files`, `list_folders`, `search_files`, `search_folders`, `create_folder`, `upload_file`, `download_file`, `upload_folder`, `delete_file` / `delete_folder`, `share`, `unshare`, `list_permissions`, `get_share_link`
- **Sheets:** `create_spreadsheet`, `get_spreadsheet`, `read_values`, `write_values`, `append_values`
- **Calendar:** `list_events`, `create_event`, `get_event`, `delete_event`
- **Docs:** `create_document`, `get_document`, `append_text`, `insert_text`
- **Slides:** `create_presentation`, `get_presentation`, `add_slide`

Declared on `DriveAPI` / `SheetsAPI` / … protocols so `client.drive.` suggests shortcuts **and** managers, with hover docstrings.

### Changed

#### OAuth token storage

- Default OAuth token path is now `./token.json` in the **current working directory** (project folder), not `%APPDATA%\googlekit\`
- Optional `user_config_token_path()` keeps the old OS user-config location if you want it
- `GoogleKit.auto(..., token_path=...)` is supported; omit `token_path` to use `./token.json`
- `token.json` remains gitignored — do not commit it

#### IDE autocomplete (service managers + shortcuts)

- `client.drive` / `client.sheets` / … are typed as service protocols (`DriveAPI`, `SheetsAPI`, …)
- After `drive.`, editors suggest **managers** (`files`, `folders`, …) **and** optional shortcuts (`list_files`, `upload_file`, …) with hover docstrings
- Same pattern for Sheets, Calendar, Docs, and Slides
- Concrete clients still have factories/provider at runtime; construct `DriveClient(...)` when you need `.provider` / `.transport` in typed code

#### ClientConfig / RetryPolicy DX

- `ClientConfig` and `RetryPolicy` are exported from the top-level `googlekit` package (`from googlekit import ClientConfig, RetryPolicy`)
- `ClientConfig(retry=5)` shorthand sets `RetryPolicy(max_attempts=5)`
- Rich class and field docstrings for IDE hover (timeout, retry fields, what gets retried, Calendar timezone, Shared Drives, etc.)

#### Docs: four auth methods

- Auth tables list **`auto()` as Method 4**, separate from `from_adc()` (not combined in one row)
- Updated in README, `docs/authentication.md`, `docs/drive.md`, `docs/index.md`, `AGENT.md`
