# Authentication

GoogleKit supports three primary credential methods plus auto-detection.

## OAuth 2.0 (desktop)

Uses the installed-app local-server flow (no deprecated OOB).

```python
from googlekit import GoogleKit

kit = GoogleKit.from_oauth(
    client_secrets="client_secret.json",
    token_path=None,  # OS user config dir by default
    services=["gdrive", "gsheets"],
    profile="readwrite",
)
```

- Tokens refresh automatically when possible
- Expanding scopes triggers reauthorization
- Default token path is under the user config directory (`FileTokenStore`), never inside the package install

See `examples/auth/oauth_desktop.py`.

## Service account

```python
from googlekit import GoogleKit

kit = GoogleKit.from_service_account(
    credentials_file="service-account.json",
    subject=None,  # set for Workspace domain-wide delegation
    services=["gsheets"],
)
```

!!! important
    Ordinary service accounts do **not** automatically access a personal user's files.
    Share Drive/Sheets resources with the service account email, or configure
    Workspace domain-wide delegation and pass `subject`.

See `examples/auth/service_account.py`.

## Application Default Credentials (ADC)

```python
from googlekit import GoogleKit

kit = GoogleKit.from_adc(
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

See `examples/auth/adc.py`.

## Auto-detect

```python
kit = GoogleKit.auto(services=["gdrive"])
```

Order: try ADC → look for `service_account.json` / `client_secrets.json` (and variants) in the working directory → raise `AuthenticationError` with guidance.

## Sharing credentials

```python
from googlekit.client import share_provider

provider = share_provider(kit)
# Pass the same provider into individual service clients
```

## Security

- Never commit secrets or tokens
- Never log credential JSON or tokens
- Restrict file permissions where supported
- Prefer least-privilege scopes
