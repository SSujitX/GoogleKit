# Installation

## Requirements

- Python 3.11–3.14
- [uv](https://docs.astral.sh/uv/)

## Install

```bash
uv add googlekit
```

This installs GoogleKit plus the Google API client libraries used by Drive, Sheets, Calendar, Docs, and Slides.

## Broken environments

If client libraries were removed or the environment is incomplete, service calls raise `MissingExtraError`:

```text
Google Drive support requires Google client libraries.
Install or reinstall with:
    uv add googlekit
```

## Development install

```bash
git clone https://github.com/SSujitX/GoogleKit.git
cd GoogleKit
uv sync --group dev
```
