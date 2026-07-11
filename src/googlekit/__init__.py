"""GoogleKit — unofficial Python SDK for Google Workspace APIs.

This package is not affiliated with, endorsed by, or sponsored by Google.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from googlekit.client import GoogleKit
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

try:
    __version__ = version("googlekit")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "dev"

__all__ = [
    "APIError",
    "AuthenticationError",
    "AuthorizationError",
    "ConfigurationError",
    "ConflictError",
    "GoogleKit",
    "GoogleKitError",
    "InsufficientScopesError",
    "MissingExtraError",
    "NotFoundError",
    "PartialFailureError",
    "QuotaExceededError",
    "RateLimitError",
    "RetryExhaustedError",
    "TransportError",
    "ValidationError",
    "__version__",
]
