# Errors

All library errors derive from `GoogleKitError`.
Site: [https://ssujitx.github.io/GoogleKit/](https://ssujitx.github.io/GoogleKit/).

```text
GoogleKitError
├── ConfigurationError
│   └── MissingExtraError
├── AuthenticationError
├── AuthorizationError
│   └── InsufficientScopesError
├── APIError
│   ├── NotFoundError
│   ├── ConflictError
│   ├── RateLimitError
│   └── QuotaExceededError
├── ValidationError
├── RetryExhaustedError
├── TransportError
└── PartialFailureError
```

## Mapping

HTTP/API failures from `googleapiclient` are mapped by `map_http_error`:

| Status | Exception |
| ------ | --------- |
| 404 | `NotFoundError` |
| 409 / 412 | `ConflictError` |
| 429 | `RateLimitError` (honors `Retry-After` when present) |
| 403 + quota reason | `QuotaExceededError` |
| other | `APIError` |

`APIError` preserves `status_code`, `reason`, and `request_id` when available.
Authorization headers and tokens are never included in messages.

## Retries

Transient failures (429, 5xx, and resumable upload/download chunk errors) are retried
per `ClientConfig.retry` / `RetryPolicy`. When attempts are exhausted, GoogleKit raises
`RetryExhaustedError` with the original exception in `last_error`.

```python
from googlekit.core.configuration import ClientConfig
from googlekit.core.retries import RetryPolicy
from googlekit.gdrive import DriveClient

drive = DriveClient.from_oauth(
    "client_secrets.json",
    config=ClientConfig(retry=RetryPolicy(max_attempts=5)),
)
```

## Missing client libraries

```python
from googlekit.core.exceptions import MissingExtraError

# Message includes: uv add googlekit
```

This only appears if Google client libraries were removed from a broken environment;
they ship with the default `googlekit` install.

## Validation

Local input failures raise `ValidationError` before a network call when practical
(empty IDs, missing paths, non-positive sizes, all-day end not exclusive, etc.).

## Example

```python
from googlekit import GoogleKit
from googlekit.core.exceptions import GoogleKitError, NotFoundError, ValidationError

client = GoogleKit.auto(services=["gdrive"])

try:
    client.drive.files.get("missing-id")
except NotFoundError as exc:
    print(exc)
except ValidationError as exc:
    print(exc)
except GoogleKitError as exc:
    print(exc)
```
