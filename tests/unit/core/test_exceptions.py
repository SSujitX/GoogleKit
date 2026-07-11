"""Exception hierarchy and HTTP error mapping."""

from __future__ import annotations

from types import SimpleNamespace

from googlekit.core.exceptions import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    ConflictError,
    GoogleKitError,
    InsufficientScopesError,
    MissingExtraError,
    NotFoundError,
    PartialFailureError,
    QuotaExceededError,
    RateLimitError,
    RetryExhaustedError,
    TransportError,
    ValidationError,
)
from googlekit.core.transport import map_http_error


def test_hierarchy() -> None:
    assert issubclass(ConfigurationError, GoogleKitError)
    assert issubclass(MissingExtraError, ConfigurationError)
    assert issubclass(AuthenticationError, GoogleKitError)
    assert issubclass(AuthorizationError, GoogleKitError)
    assert issubclass(InsufficientScopesError, AuthorizationError)
    assert issubclass(NotFoundError, APIError)
    assert issubclass(ConflictError, APIError)
    assert issubclass(RateLimitError, APIError)
    assert issubclass(QuotaExceededError, APIError)
    assert issubclass(ValidationError, GoogleKitError)
    assert issubclass(RetryExhaustedError, GoogleKitError)
    assert issubclass(TransportError, GoogleKitError)
    assert issubclass(PartialFailureError, GoogleKitError)


def test_insufficient_scopes_message() -> None:
    err = InsufficientScopesError(
        "Need broader access",
        required_scopes=["https://www.googleapis.com/auth/drive"],
        granted_scopes=["https://www.googleapis.com/auth/drive.file"],
    )
    assert "Need broader access" in str(err)
    assert "drive" in str(err)
    assert "Reauthorize" in str(err)


def test_api_error_parts() -> None:
    err = APIError("boom", status_code=500, reason="backendError", request_id="abc")
    text = str(err)
    assert "HTTP 500" in text
    assert "backendError" in text
    assert "abc" in text


def test_partial_failure() -> None:
    err = PartialFailureError("partial", succeeded=[1], failed=[2])
    assert err.succeeded == [1]
    assert err.failed == [2]


def _http_exc(status: int, *, reason: str = "err", headers: dict | None = None) -> Exception:
    resp = SimpleNamespace(status=status, headers=headers or {})
    exc: Exception = Exception(reason)
    exc.resp = resp  # type: ignore[attr-defined]
    exc._get_reason = lambda: reason  # type: ignore[attr-defined]
    return exc


def test_map_http_error_404() -> None:
    mapped = map_http_error(_http_exc(404, reason="Not Found"))
    assert isinstance(mapped, NotFoundError)
    assert mapped.status_code == 404


def test_map_http_error_409() -> None:
    mapped = map_http_error(_http_exc(409))
    assert isinstance(mapped, ConflictError)


def test_map_http_error_429_retry_after() -> None:
    mapped = map_http_error(
        _http_exc(429, reason="rateLimitExceeded", headers={"Retry-After": "3.5"})
    )
    assert isinstance(mapped, RateLimitError)
    assert mapped.retry_after == 3.5


def test_map_http_error_quota() -> None:
    mapped = map_http_error(_http_exc(403, reason="Quota exceeded for metric"))
    assert isinstance(mapped, QuotaExceededError)


def test_map_http_error_generic() -> None:
    mapped = map_http_error(_http_exc(500, reason="internal", headers={"x-goog-request-id": "rid"}))
    assert isinstance(mapped, APIError)
    assert mapped.status_code == 500
    assert mapped.request_id == "rid"
