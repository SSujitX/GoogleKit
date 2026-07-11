# Errors

All library errors derive from `GoogleKitError`.

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

## Missing client libraries

```python
from googlekit.core.exceptions import MissingExtraError

# Message includes: uv add googlekit
```

## Validation

Local input failures raise `ValidationError` before a network call when practical
(empty IDs, missing paths, non-positive sizes, etc.).

## Retries

Transient failures may be retried per `RetryPolicy`. When attempts are exhausted,
`RetryExhaustedError` is raised with the attempt count and last error chained.
