"""Core retries, pagination, optional extras."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from googlekit.core.exceptions import MissingExtraError, RateLimitError, ValidationError
from googlekit.core.optional import installed_extras, require_extra
from googlekit.core.pagination import Page, PageIterator
from googlekit.core.retries import RetryPolicy, call_with_retries, should_retry_status
from googlekit.core.validation import require_non_empty, require_positive_int


def test_should_retry_status() -> None:
    assert should_retry_status(429)
    assert should_retry_status(503)
    assert not should_retry_status(400)
    assert not should_retry_status(None)


def test_call_with_retries_succeeds_after_transient() -> None:
    sleeps: list[float] = []
    state = {"n": 0}

    def flaky() -> str:
        state["n"] += 1
        if state["n"] < 3:
            raise RateLimitError("slow down", retry_after=0.01)
        return "ok"

    result = call_with_retries(
        flaky,
        policy=RetryPolicy(max_attempts=5, initial_delay=0.01, jitter=0),
        sleep=sleeps.append,
    )
    assert result == "ok"
    assert len(sleeps) == 2


def test_call_with_retries_exhausted() -> None:
    def always_fail() -> None:
        raise RateLimitError("nope")

    with pytest.raises(RateLimitError):
        call_with_retries(
            always_fail,
            policy=RetryPolicy(max_attempts=2, initial_delay=0.01, jitter=0),
            sleep=lambda _d: None,
        )


def test_page_iterator_lazy() -> None:
    calls = {"n": 0}

    def fetch(token: str | None, size: int) -> Page[int]:
        calls["n"] += 1
        if token is None:
            return Page(items=[1, 2], next_page_token="t2")
        return Page(items=[3], next_page_token=None)

    it = PageIterator(fetch, page_size=2)
    assert calls["n"] == 0
    assert next(it) == 1
    assert calls["n"] == 1
    assert list(it) == [2, 3]
    assert calls["n"] == 2


def test_missing_extra_message() -> None:
    with patch("googlekit.core.optional.import_module", side_effect=ImportError("x")):
        with pytest.raises(MissingExtraError) as exc:
            require_extra("gdrive")
        assert 'uv add "googlekit[gdrive]"' in str(exc.value)


def test_installed_extras_keys() -> None:
    result = installed_extras()
    assert set(result) >= {"gdrive", "gsheets", "gcalendar", "gdocs", "gslides"}


def test_validation() -> None:
    assert require_non_empty("abc", "name") == "abc"
    with pytest.raises(ValidationError):
        require_non_empty("  ", "name")
    assert require_positive_int(3, "n") == 3
    with pytest.raises(ValidationError):
        require_positive_int(0, "n")
