"""Base package importability and public surface."""

from __future__ import annotations

import googlekit
from googlekit import GoogleKit
from googlekit.core.exceptions import MissingExtraError


def test_import_googlekit() -> None:
    assert googlekit.__version__
    assert GoogleKit is not None


def test_public_exceptions_exported() -> None:
    assert issubclass(MissingExtraError, Exception)
    assert hasattr(googlekit, "AuthenticationError")
    assert hasattr(googlekit, "ValidationError")


def test_core_imports_without_service_modules() -> None:
    from googlekit.auth.scopes import ScopeSet
    from googlekit.core.configuration import ClientConfig
    from googlekit.core.pagination import Page

    assert ScopeSet is not None
    assert ClientConfig is not None
    assert Page is not None
