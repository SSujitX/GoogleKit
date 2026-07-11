"""Shared fakes for Sheets/Calendar unit tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock


class FakeRequest:
    def __init__(self, result: Any = None, error: Exception | None = None) -> None:
        self._result = result
        self._error = error
        self.executed = False

    def execute(self) -> Any:
        self.executed = True
        if self._error:
            raise self._error
        return self._result


class FakeProvider:
    def __init__(self, scopes: frozenset[str] | None = None) -> None:
        self._scopes = scopes or frozenset()

    def credentials(self) -> Any:
        return object()

    def scopes(self) -> frozenset[str]:
        return self._scopes


def chain_mock(**leaf_methods: Any) -> MagicMock:
    """Build a nested MagicMock service where leaf methods return FakeRequests.

    Example::
        svc = chain_mock(values_update={"spreadsheetId": "x"})
        # svc.spreadsheets().values().update(...) -> FakeRequest
    """
    root = MagicMock()
    return root
