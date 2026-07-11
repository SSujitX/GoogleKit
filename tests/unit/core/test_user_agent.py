"""Transport user-agent wrapper tests."""

from __future__ import annotations

from unittest.mock import MagicMock

from googlekit.core.transport import _UserAgentHttp


def test_user_agent_http_injects_header() -> None:
    inner = MagicMock()
    inner.request.return_value = ("resp", b"ok")
    wrapped = _UserAgentHttp(inner, "googlekit/test")
    wrapped.request("https://example.com", method="GET", headers={"Accept": "application/json"})
    kwargs = inner.request.call_args.kwargs
    headers = kwargs["headers"]
    assert headers["Accept"] == "application/json"
    assert headers["user-agent"] == "googlekit/test"


def test_user_agent_http_does_not_override_existing() -> None:
    inner = MagicMock()
    inner.request.return_value = ("resp", b"ok")
    wrapped = _UserAgentHttp(inner, "googlekit/test")
    wrapped.request("https://example.com", headers={"user-agent": "custom/1"})
    headers = inner.request.call_args.kwargs["headers"]
    assert headers["user-agent"] == "custom/1"
