"""Retry policy tests without real sleeping."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from googlekit.core.exceptions import APIError, RateLimitError, RetryExhaustedError
from googlekit.core.retries import RetryPolicy, call_with_retries, should_retry_status


def test_should_retry_status() -> None:
    assert should_retry_status(429) is True
    assert should_retry_status(503) is True
    assert should_retry_status(404) is False
    assert should_retry_status(None) is False


def test_delay_for_attempt_respects_retry_after() -> None:
    policy = RetryPolicy(jitter=0.0)
    assert policy.delay_for_attempt(0, retry_after=12.0) == 12.0
    assert policy.delay_for_attempt(0, retry_after=120.0) == policy.max_delay


def test_delay_exponential_no_jitter() -> None:
    policy = RetryPolicy(initial_delay=1.0, multiplier=2.0, jitter=0.0, max_delay=100.0)
    assert policy.delay_for_attempt(0) == 1.0
    assert policy.delay_for_attempt(1) == 2.0
    assert policy.delay_for_attempt(2) == 4.0


def test_call_with_retries_success_first_try() -> None:
    sleep = MagicMock()
    result = call_with_retries(lambda: 42, sleep=sleep)
    assert result == 42
    sleep.assert_not_called()


def test_call_with_retries_retries_rate_limit() -> None:
    sleep = MagicMock()
    calls = {"n": 0}

    def fn() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise RateLimitError("slow", retry_after=0.01)
        return "ok"

    policy = RetryPolicy(max_attempts=5, jitter=0.0)
    assert call_with_retries(fn, policy=policy, sleep=sleep) == "ok"
    assert calls["n"] == 3
    assert sleep.call_count == 2


def test_call_with_retries_disabled() -> None:
    sleep = MagicMock()

    def fn() -> None:
        raise RateLimitError("nope")

    with pytest.raises(RateLimitError):
        call_with_retries(fn, policy=RetryPolicy(enabled=False), sleep=sleep)
    sleep.assert_not_called()


def test_call_with_retries_non_retryable_raises_immediately() -> None:
    sleep = MagicMock()

    def fn() -> None:
        raise APIError("bad", status_code=400)

    with pytest.raises(APIError):
        call_with_retries(fn, policy=RetryPolicy(max_attempts=5), sleep=sleep)
    sleep.assert_not_called()


def test_call_with_retries_exhausts() -> None:
    sleep = MagicMock()

    def fn() -> None:
        raise RateLimitError("always")

    with pytest.raises(RetryExhaustedError) as exc_info:
        call_with_retries(fn, policy=RetryPolicy(max_attempts=3, jitter=0.0), sleep=sleep)
    assert sleep.call_count == 2
    assert exc_info.value.attempts == 3
    assert isinstance(exc_info.value.last_error, RateLimitError)


def test_call_with_retries_custom_predicate() -> None:
    sleep = MagicMock()
    calls = {"n": 0}

    class Transient(Exception):
        pass

    def fn() -> int:
        calls["n"] += 1
        if calls["n"] == 1:
            raise Transient("once")
        return 1

    result = call_with_retries(
        fn,
        policy=RetryPolicy(max_attempts=3, jitter=0.0),
        sleep=sleep,
        is_retryable=lambda exc: isinstance(exc, Transient),
    )
    assert result == 1
    sleep.assert_called_once()


def test_retry_exhausted_error_message() -> None:
    err = RetryExhaustedError(attempts=5, last_error=RuntimeError("x"))
    assert "5" in str(err)
    assert err.attempts == 5
