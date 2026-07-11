---
title: Authenticate GoogleKit (OAuth, ADC, service account)
description: >-
  Set up GoogleKit with four auth methods: Application Default Credentials
  (`from_adc`), service accounts, OAuth 2.0 desktop, or auto-detect (`auto`).
  Token storage and security tips.
---

# Authentication

GoogleKit supports **four** credential methods. Prefer an explicit factory in production; use `auto()` when you want discovery.

Full site: [https://ssujitx.github.io/GoogleKit/](https://ssujitx.github.io/GoogleKit/).

**Official Google docs:** [OAuth 2.0](https://developers.google.com/identity/protocols/oauth2) ·
[Installed apps](https://developers.google.com/identity/protocols/oauth2/native-app) ·
[Service accounts](https://developers.google.com/identity/protocols/oauth2/service-account) ·
[ADC](https://cloud.google.com/docs/authentication/application-default-credentials) ·
[Google Auth Platform → Clients](https://console.cloud.google.com/auth/clients) ·
[Create credentials (Workspace)](https://developers.google.com/workspace/guides/create-credentials)

## Choose a method

| Method | Factory | Best for | Setup |
| ------ | ------- | -------- | ----- |
| **1. Application Default Credentials** | `from_adc()` | Local dev, GCP | `gcloud` CLI |
| **2. Service account** | `from_service_account()` | Servers, bots, CI | JSON key file |
| **3. OAuth 2.0 desktop** | `from_oauth()` | Personal / interactive apps | Desktop client JSON + browser |
| **4. Auto-detect** | `auto()` | Quick start / any local creds | ADC **or** a JSON file in CWD |

## OAuth 2.0 desktop (Method 3)

Uses the installed-app local-server flow (no deprecated OOB).

```python
from googlekit import GoogleKit
from googlekit.auth.scopes import ScopeProfile

client = GoogleKit.from_oauth(
    client_secrets="client_secrets.json",
    token_path=None,  # defaults to ./token.json in the working directory
    services=["gdrive", "gsheets"],
    profile=ScopeProfile.READWRITE,
)
```

- Tokens refresh automatically when possible
- Expanding scopes beyond what the cached token was granted requires a new browser consent flow (installed apps do not support incremental authorization)
- GoogleKit checks `granted_scopes` after granular consent. A full Drive or
  Calendar grant also satisfies requests for the corresponding narrower scopes.
- Default token path is under the **current working directory** (`./token.json`) via `FileTokenStore`; pass `token_path=` to override, or use `user_config_token_path()` for `%APPDATA%` / XDG
- Token files are written atomically with restrictive permissions when the OS supports them

**Cloud Console setup (summary):**

1. Create a project and enable the APIs you need ([Library](https://console.cloud.google.com/apis/library))
2. Configure **[Google Auth Platform](https://console.cloud.google.com/auth/overview)**: [Branding](https://console.cloud.google.com/auth/branding), [Audience](https://console.cloud.google.com/auth/audience) (add yourself as a test user while testing), optional [Data Access](https://console.cloud.google.com/auth/scopes)
3. **[Clients](https://console.cloud.google.com/auth/clients) → + Create client → Desktop app**
4. Download JSON → save as `client_secrets.json`

(If you still see the older UI: APIs & Services → OAuth consent screen + Credentials → OAuth client ID.)

See `examples/auth/oauth_desktop.py`.

## Service account (Method 2)

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

## Application Default Credentials (Method 1)

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

## Auto-detect (Method 4)

```python
client = GoogleKit.auto(services=["gdrive"])
# Optional: token_path=... when discovery lands on OAuth
```

Order:

1. Try ADC (`from_adc` path)
2. Look for service-account JSON in the working directory (`service_account.json`, `service_account_key.json`, `sa_credentials.json`)
3. Look for OAuth client JSON (`client_secrets.json`, `client_secret.json`, `credentials.json`, `oauth_credentials.json`)
4. Raise `AuthenticationError` with setup guidance

Prefer explicit `from_adc()` / `from_service_account()` / `from_oauth()` when you know the credential type.

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
