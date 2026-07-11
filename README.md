# GoogleKit

**Unofficial** Python SDK for Google Drive, Sheets, Calendar, Docs, and Slides.

> GoogleKit is **not** affiliated with, endorsed by, or sponsored by Google LLC.

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Supported services

| Service | Import |
|---------|--------|
| Google Drive | `googlekit.gdrive` |
| Google Sheets | `googlekit.gsheets` |
| Google Calendar | `googlekit.gcalendar` |
| Google Docs | `googlekit.gdocs` |
| Google Slides | `googlekit.gslides` |

## Installation (uv)

```bash
uv add googlekit
```

This installs GoogleKit and the Google API client libraries needed for all services.

## Quick start

### Unified client

```python
from googlekit import GoogleKit

kit = GoogleKit.from_oauth(
    client_secrets="client_secrets.json",
    token_path="token.json",
    services=["gdrive", "gsheets"],
)

files = kit.drive.files.list()
kit.sheets.values.read("spreadsheet_id", "Sheet1!A1:D20")
```

### Auto-detect credentials (PyDrive4-style)

```python
from googlekit import GoogleKit

# Tries ADC, then service_account.json / client_secrets.json in cwd
kit = GoogleKit.auto(services=["gdrive"])
```

### Individual clients

```python
from googlekit.gdrive import DriveClient

drive = DriveClient.from_oauth("client_secrets.json")
drive.files.upload_path("report.pdf")
```

## Authentication

| Method | Factory | Best for |
|--------|---------|----------|
| OAuth desktop | `from_oauth(...)` | Personal Drive / interactive |
| Service account | `from_service_account(...)` | Servers, bots (share files with SA email) |
| ADC | `from_adc(...)` | `gcloud auth application-default login` / GCP |

**Security:** never commit `client_secrets.json`, service-account keys, or `token.json`. Tokens default to an OS user config directory.

Enable the APIs you need in Google Cloud Console (Drive, Sheets, Calendar, Docs, Slides).

## OAuth scopes

GoogleKit uses **least privilege** presets (`metadata`, `readonly`, `readwrite`, `full`) per service. It does not request all scopes by default. Missing scopes raise `InsufficientScopesError`.

## Development

```bash
uv sync --group dev
uv run pytest -m "not integration"
uv build
```

## CLI

```bash
uv run googlekit --version
uv run googlekit doctor
uv run googlekit auth status
```

## License

MIT — see [LICENSE](LICENSE).

## Disclaimer

This is an independent open-source project. Google and Google Workspace are trademarks of Google LLC.
