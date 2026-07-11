---
title: Authenticate GoogleKit (OAuth, ADC, service account)
description: >-
  Set up Google OAuth 2.0 desktop flow, Application Default Credentials, or
  service accounts with GoogleKit. Token storage, auto-detect, and security tips.
---

# Authentication

GoogleKit supports three primary credential methods plus auto-detection.
Full site: [https://ssujitx.github.io/GoogleKit/](https://ssujitx.github.io/GoogleKit/).

**Official Google docs:** [OAuth 2.0](https://developers.google.com/identity/protocols/oauth2) ·
[Installed apps](https://developers.google.com/identity/protocols/oauth2/native-app) ·
[Service accounts](https://developers.google.com/identity/protocols/oauth2/service-account) ·
[ADC](https://cloud.google.com/docs/authentication/application-default-credentials) ·
[Cloud Console credentials](https://console.cloud.google.com/apis/credentials)

## Choose a method

| Method | Factory | Best for |
| ------ | ------- | -------- |
| Application Default Credentials | `from_adc()` / `auto()` | Local dev, GCP |
| Service account | `from_service_account()` | Servers, bots, CI |
| OAuth 2.0 desktop | `from_oauth()` | Personal Drive / interactive apps |

## OAuth 2.0 (desktop)

Uses the installed-app local-server flow (no deprecated OOB).

```python
from googlekit import GoogleKit
from googlekit.auth.scopes import ScopeProfile

client = GoogleKit.from_oauth(
    client_secrets="client_secrets.json",
    token_path=None,  # OS user config dir by default
    services=["gdrive", "gsheets"],
    profile=ScopeProfile.READWRITE,
)
```

- Tokens refresh automatically when possible
- Expanding scopes beyond what the cached token was granted requires a new browser consent flow (installed apps do not support incremental authorization)
- Default token path is under the user config directory (`FileTokenStore`), never inside the package install
- Token files are written atomically with restrictive permissions when the OS supports them

**Cloud Console setup (summary):**

1. Create a project and enable the APIs you need
2. Configure the OAuth consent screen (add yourself as a test user while testing)
3. Create credentials → **OAuth client ID** → **Desktop app**
4. Download JSON → save as `client_secrets.json`

See `examples/auth/oauth_desktop.py`.

## Service account

```python
from googlekit import GoogleKit

client = GoogleKit.from_service_account(
    credentials_file="service_account.json",
    subject=None,  # set for Workspace domain-wide delegation
    services=["gsheets", "gdrive"],
)
```

!!! important
    Ordinary service accounts do **not** automatically access a personal user's files.
    Share Drive/Sheets/Docs/Slides resources with the service account email, or configure
    Workspace domain-wide delegation and pass `subject`.

If your org blocks key creation (`iam.disableServiceAccountKeyCreation`), use OAuth or ADC instead.

See `examples/auth/service_account.py`.

## Application Default Credentials (ADC)

```python
from googlekit import GoogleKit

client = GoogleKit.from_adc(
    quota_project_id=None,
    services=["gcalendar"],
)
```

Typical setup:

```bash
gcloud auth application-default login
# or
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

ADC order: `GOOGLE_APPLICATION_CREDENTIALS` → gcloud user ADC → GCE/Cloud Run metadata.

See `examples/auth/adc.py`.

## Auto-detect

```python
client = GoogleKit.auto(services=["gdrive"])
```

Order:

1. Try ADC
2. Look for service-account JSON in the working directory (`service_account.json`, `service_account_key.json`, `sa_credentials.json`)
3. Look for OAuth client JSON (`client_secrets.json`, `client_secret.json`, `credentials.json`, `oauth_credentials.json`)
4. Raise `AuthenticationError` with setup guidance

## Per-service clients

```python
from googlekit.gdrive import DriveClient
from googlekit.gsheets import SheetsClient

drive = DriveClient.from_oauth("client_secrets.json")
sheets = SheetsClient.from_service_account("service_account.json")
```

Same factories exist on `CalendarClient`, `DocsClient`, and `SlidesClient`.

## Sharing credentials across clients

```python
from googlekit import GoogleKit
from googlekit.client import share_provider
from googlekit.gdrive import DriveClient

client = GoogleKit.auto(services=["gdrive", "gsheets"])
provider = share_provider(client)
drive = DriveClient(provider)
```

## CLI helpers

```bash
uv run googlekit doctor
uv run googlekit auth status
```

These print non-secret status only (credential file detected, token present, client libraries installed).

## Security

- Never commit secrets or tokens
- Never log credential JSON or tokens
- Restrict file permissions where supported
- Prefer least-privilege scopes (see [Scopes](scopes.md))
- Public Drive sharing requires an explicit `public=True` guard in GoogleKit
