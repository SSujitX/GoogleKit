## [0.0.3] - 2026-07-12

### Changed

#### OAuth token storage

- Default OAuth token path is now `./token.json` in the **current working directory** (project folder), not `%APPDATA%\googlekit\`
- Optional `user_config_token_path()` keeps the old OS user-config location if you want it
- `GoogleKit.auto(..., token_path=...)` is supported; omit `token_path` to use `./token.json`
- `token.json` remains gitignored — do not commit it

#### IDE autocomplete (service managers)

- `client.drive` / `client.sheets` / `client.calendar` / `client.docs` / `client.slides` are typed as service protocols (`DriveAPI`, `SheetsAPI`, …)
- After `drive.`, editors suggest **managers** (`files`, `folders`, `permissions`, `changes`) instead of auth factories (`from_oauth`, `from_provider`) or internals (`provider`, `transport`)
- Same for Sheets (`spreadsheets`, `values`, `worksheets`, `formatting`), Calendar, Docs, and Slides
- Concrete clients still have factories/provider at runtime; construct `DriveClient(...)` when you need `.provider` / `.transport` in typed code

#### ClientConfig / RetryPolicy DX

- `ClientConfig` and `RetryPolicy` are exported from the top-level `googlekit` package (`from googlekit import ClientConfig, RetryPolicy`)
- `ClientConfig(retry=5)` shorthand sets `RetryPolicy(max_attempts=5)`
- Rich class and field docstrings for IDE hover (timeout, retry fields, what gets retried, Calendar timezone, Shared Drives, etc.)

#### Public API hover docs

- Expanded docstrings on `GoogleKit` factories/properties, `DriveClient` managers, `ScopeProfile` / `ScopeSet`, `Page` / `PageIterator`, and `FilesManager.list` (including empty-list / `drive.file` tip)
- Service client class docs call out managers and key pitfalls (Calendar timezone, Docs UTF-16, Drive scopes)
