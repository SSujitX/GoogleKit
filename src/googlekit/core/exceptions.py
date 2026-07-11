"""Shared exception hierarchy for GoogleKit."""

from __future__ import annotations

from typing import Any


class GoogleKitError(Exception):
    """Base exception for all GoogleKit errors."""

    def __init__(self, message: str = "An error occurred in GoogleKit") -> None:
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        return self.message


class ConfigurationError(GoogleKitError):
    """Raised when configuration is missing or invalid."""


class AuthenticationError(GoogleKitError):
    """Raised when credentials cannot be obtained or are invalid."""


class AuthorizationError(GoogleKitError):
    """Raised when the caller is authenticated but not permitted."""


class InsufficientScopesError(AuthorizationError):
    """Raised when granted OAuth scopes do not cover a requested operation."""

    def __init__(
        self,
        message: str,
        *,
        required_scopes: list[str] | None = None,
        granted_scopes: list[str] | None = None,
    ) -> None:
        self.required_scopes = required_scopes or []
        self.granted_scopes = granted_scopes or []
        hint = ""
        if self.required_scopes:
            joined = ", ".join(self.required_scopes)
            hint = f" Required scope(s): {joined}. Reauthorize with the additional scopes."
        super().__init__(f"{message}{hint}")


class MissingExtraError(ConfigurationError):
    """Raised when Google client libraries cannot be imported."""

    def __init__(self, service: str, extra: str) -> None:
        self.service = service
        self.extra = extra
        super().__init__(
            f"{service} support requires Google client libraries.\n"
            f"Install or reinstall with:\n"
            f"    uv add googlekit"
        )


class APIError(GoogleKitError):
    """Raised when a Google API returns an error response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        reason: str | None = None,
        request_id: str | None = None,
        details: Any = None,
    ) -> None:
        self.status_code = status_code
        self.reason = reason
        self.request_id = request_id
        self.details = details
        parts = [message]
        if status_code is not None:
            parts.append(f"(HTTP {status_code})")
        if reason:
            parts.append(f"reason={reason}")
        if request_id:
            parts.append(f"request_id={request_id}")
        super().__init__(" ".join(parts))


class NotFoundError(APIError):
    """Raised when a requested resource does not exist."""


class ConflictError(APIError):
    """Raised on conflicting resource state (e.g. precondition failed)."""


class ValidationError(GoogleKitError):
    """Raised when caller input fails local validation."""


class RateLimitError(APIError):
    """Raised when the API rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        *,
        retry_after: float | None = None,
        status_code: int | None = 429,
        reason: str | None = None,
        request_id: str | None = None,
        details: Any = None,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(
            message,
            status_code=status_code,
            reason=reason,
            request_id=request_id,
            details=details,
        )


class QuotaExceededError(APIError):
    """Raised when project quota is exhausted."""


class RetryExhaustedError(GoogleKitError):
    """Raised when all retry attempts for a transient failure are exhausted."""

    def __init__(
        self,
        message: str = "Retry attempts exhausted",
        *,
        attempts: int | None = None,
        last_error: BaseException | None = None,
    ) -> None:
        self.attempts = attempts
        self.last_error = last_error
        suffix = f" after {attempts} attempts" if attempts is not None else ""
        super().__init__(f"{message}{suffix}")
        if last_error is not None:
            self.__cause__ = last_error


class TransportError(GoogleKitError):
    """Raised on network/transport failures talking to Google APIs."""


class PartialFailureError(GoogleKitError):
    """Raised when a batch/bulk operation partially succeeds."""

    def __init__(
        self,
        message: str,
        *,
        succeeded: list[Any] | None = None,
        failed: list[Any] | None = None,
    ) -> None:
        self.succeeded = succeeded or []
        self.failed = failed or []
        super().__init__(message)
