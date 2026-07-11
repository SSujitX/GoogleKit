# GoogleKit

Unofficial Python SDK for **Google Drive**, **Sheets**, **Calendar**, **Docs**, and **Slides**.

!!! warning "Unofficial"
    GoogleKit is not affiliated with, endorsed by, or sponsored by Google.
    Google trademarks remain the property of their owners.

## Why GoogleKit?

- One consistent API across five Workspace products
- Optional extras so installs stay lean
- OAuth, service accounts, and ADC with shared credentials
- Least-privilege scope presets
- Retries, lazy pagination, and actionable errors

## Quick links

- [Installation](installation.md)
- [Authentication](authentication.md)
- [Scopes](scopes.md)
- [Errors](errors.md)
- [Publishing to PyPI](publishing.md)

```python
from googlekit import GoogleKit

kit = GoogleKit.from_oauth("client_secret.json", services=["gdrive"])
kit.drive.files.upload("report.pdf")
```
