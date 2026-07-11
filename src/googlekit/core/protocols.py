"""Shared protocols."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class CredentialProvider(Protocol):
    """Produces Google credentials for API clients."""

    def credentials(self) -> Any:
        """Return a google.auth credentials object."""
        ...

    def scopes(self) -> frozenset[str]:
        """Return the scopes associated with the credentials."""
        ...


@runtime_checkable
class TokenStore(Protocol):
    """Persists OAuth tokens without logging secrets."""

    def load(self) -> str | None:
        """Load serialized token JSON, or None if absent."""
        ...

    def save(self, token_json: str) -> None:
        """Persist serialized token JSON."""
        ...

    def clear(self) -> None:
        """Remove any stored token."""
        ...
