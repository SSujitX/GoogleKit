---
title: Install GoogleKit (pip / uv)
description: >-
  Install the unofficial GoogleKit Python SDK for Drive, Sheets, Calendar, Docs,
  and Slides. Requires Python 3.11+. Google API client libraries included by default.
---

# Installation

## Requirements

- Python **3.11–3.14**
- [pip](https://pip.pypa.io/) or [uv](https://docs.astral.sh/uv/) (recommended)

## Install

```bash
pip install googlekit
```

Or with UV:

```bash
uv add googlekit
```

This installs GoogleKit plus the Google API client libraries used by Drive, Sheets, Calendar, Docs, and Slides. No extras are required for those services.

## Enable Google APIs

In [Google Cloud Console → Library](https://console.cloud.google.com/apis/library), enable only the APIs you use:

| Product | Console / docs |
| ------- | -------------- |
| Drive | [Enable Drive API](https://console.cloud.google.com/apis/library/drive.googleapis.com) · [Drive docs](https://developers.google.com/workspace/drive/api/guides/about-sdk) |
| Sheets | [Enable Sheets API](https://console.cloud.google.com/apis/library/sheets.googleapis.com) · [Sheets docs](https://developers.google.com/workspace/sheets/api/guides/concepts) |
| Calendar | [Enable Calendar API](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com) · [Calendar docs](https://developers.google.com/workspace/calendar/api/guides/overview) |
| Docs | [Enable Docs API](https://console.cloud.google.com/apis/library/docs.googleapis.com) · [Docs docs](https://developers.google.com/workspace/docs/api/how-tos/overview) |
| Slides | [Enable Slides API](https://console.cloud.google.com/apis/library/slides.googleapis.com) · [Slides docs](https://developers.google.com/workspace/slides/api/guides/overview) |

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

Docs site builds:

```bash
uv run mkdocs build --strict
```

On the Docs GitHub Actions workflow (`GOOGLEKIT_SOCIAL_CARDS=true`), Material generates [social cards](https://squidfunk.github.io/mkdocs-material/setup/setting-up-social-cards/) (Cairo is available on Ubuntu runners). Local Windows builds skip card images by default.
