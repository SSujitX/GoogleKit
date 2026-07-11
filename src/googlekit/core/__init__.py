"""Core package exports."""

from __future__ import annotations

from googlekit.core.configuration import ClientConfig
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
from googlekit.core.pagination import Page, PageIterator
from googlekit.core.retries import RetryPolicy

__all__ = [
    "APIError",
    "AuthenticationError",
    "AuthorizationError",
    "ClientConfig",
    "ConfigurationError",
    "ConflictError",
    "GoogleKitError",
    "InsufficientScopesError",
    "MissingExtraError",
    "NotFoundError",
    "Page",
    "PageIterator",
    "PartialFailureError",
    "QuotaExceededError",
    "RateLimitError",
    "RetryExhaustedError",
    "RetryPolicy",
    "TransportError",
    "ValidationError",
]
