# Installation

GoogleKit uses optional extras. The base package imports without Google API client libraries.

## Requirements

- Python 3.11–3.14
- [uv](https://docs.astral.sh/uv/)

## Commands

```bash
uv add googlekit
uv add "googlekit[gdrive]"
uv add "googlekit[gsheets]"
uv add "googlekit[gcalendar]"
uv add "googlekit[gdocs]"
uv add "googlekit[gslides]"
uv add "googlekit[all]"
```

| Extra | Purpose |
| ----- | ------- |
| *(base)* | Auth, core types, exceptions, CLI |
| `gdrive` | Drive client and managers |
| `gsheets` | Sheets client and managers |
| `gcalendar` | Calendar client and managers |
| `gdocs` | Docs client and managers |
| `gslides` | Slides client and managers |
| `all` | Union of all service dependencies |

## Missing extras

```python
from googlekit import GoogleKit

kit = GoogleKit.from_oauth("client_secret.json")
kit.drive  # raises MissingExtraError if [gdrive] is not installed
```

Example message:

```text
Google Drive support is not installed.
Install it with:
    uv add "googlekit[gdrive]"
```

## Development install

```bash
git clone https://github.com/SSujitX/GoogleKit.git
cd GoogleKit
uv sync --all-extras
```
