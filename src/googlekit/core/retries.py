"""Retry policy with injectable clock for tests."""

from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from googlekit.core.constants import DEFAULT_MAX_RETRIES
from googlekit.core.exceptions import RateLimitError, RetryExhaustedError

logger = logging.getLogger(__name__)

T = TypeVar("T")

SleepFn = Callable[[float], None]
ClockFn = Callable[[], float]


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Exponential backoff with jitter for transient Google API failures.

    Retried by default:

    - HTTP 429 and selected 403 rate-limit reasons
    - HTTP 408 / 500 / 502 / 503 / 504
    - Transport / connection / timeout errors

    Not retried: 404, validation errors, most other 4xx, auth failures.

    When attempts are exhausted, GoogleKit raises
    :class:`~googlekit.core.exceptions.RetryExhaustedError`.

    Prefer the shorthand on config for simple cases::

        from googlekit import ClientConfig
        ClientConfig(retry=5)  # → RetryPolicy(max_attempts=5)

    Full control::

        from googlekit import ClientConfig, RetryPolicy
        ClientConfig(retry=RetryPolicy(max_attempts=8, initial_delay=1.0, jitter=0.1))
    """

    max_attempts: int = DEFAULT_MAX_RETRIES
    """Total tries including the first attempt (default 5). Use 1 to effectively disable."""

    initial_delay: float = 0.5
    """Base delay in seconds before the first retry (grows with ``multiplier``)."""

    max_delay: float = 60.0
    """Cap on sleep seconds between attempts (also caps ``Retry-After`` when present)."""

    multiplier: float = 2.0
    """Exponential growth factor applied to ``initial_delay`` per attempt."""

    jitter: float = 0.2
    """Randomization fraction of the computed delay (0 disables jitter). Reduces thundering herds."""

    enabled: bool = True
    """When False, the operation runs once with no backoff (same idea as ``max_attempts=1``)."""

    def delay_for_attempt(self, attempt: int, *, retry_after: float | None = None) -> float:
        """Compute sleep seconds for a 0-based attempt index."""
        if retry_after is not None and retry_after > 0:
            return min(retry_after, self.max_delay)
        base = min(self.initial_delay * (self.multiplier**attempt), self.max_delay)
        if self.jitter <= 0:
            return base
        spread = base * self.jitter
        return max(0.0, base + random.uniform(-spread, spread))


def should_retry_status(status: int | None) -> bool:
    """Return True for transient HTTP statuses."""
    if status is None:
        return False
    return status in {408, 429, 500, 502, 503, 504}


def call_with_retries(
    fn: Callable[[], T],
    *,
    policy: RetryPolicy | None = None,
    sleep: SleepFn = time.sleep,
    is_retryable: Callable[[BaseException], bool] | None = None,
) -> T:
    """Execute ``fn`` with retries on transient failures.

    Args:
        fn: Zero-arg callable performing the operation.
        policy: Retry configuration. ``enabled=False`` disables retries.
        sleep: Injectable sleep (tests pass a no-op).
        is_retryable: Optional predicate; defaults to RateLimitError / status checks.

    Returns:
        The result of ``fn``.

    Raises:
        RetryExhaustedError: When retryable failures exhaust ``max_attempts``.
            The original exception is available as ``last_error``.
        BaseException: Non-retryable errors are re-raised immediately.
    """
    policy = policy or RetryPolicy()
    if not policy.enabled or policy.max_attempts <= 1:
        return fn()

    last_error: BaseException | None = None
    for attempt in range(policy.max_attempts):
        try:
            return fn()
        except BaseException as exc:
            last_error = exc
            retryable = (
                is_retryable(exc) if is_retryable is not None else _default_is_retryable(exc)
            )
            if not retryable:
                raise
            if attempt >= policy.max_attempts - 1:
                raise RetryExhaustedError(
                    attempts=policy.max_attempts,
                    last_error=exc,
                ) from exc
            retry_after = getattr(exc, "retry_after", None)
            delay = policy.delay_for_attempt(
                attempt,
                retry_after=retry_after if isinstance(retry_after, (int, float)) else None,
            )
            logger.debug(
                "Retrying after %.2fs (attempt %s/%s): %s",
                delay,
                attempt + 1,
                policy.max_attempts,
                type(exc).__name__,
            )
            sleep(delay)

    raise RetryExhaustedError(
        attempts=policy.max_attempts,
        last_error=last_error,
    )


def _default_is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, RateLimitError):
        return True
    # Network / transport failures (timeouts, resets, DNS) are transient.
    from googlekit.core.exceptions import TransportError

    if isinstance(exc, TransportError):
        return True
    if isinstance(exc, (TimeoutError, ConnectionError, OSError)):
        return True
    status = getattr(exc, "status_code", None)
    if isinstance(status, int) and should_retry_status(status):
        return True
    # googleapiclient HttpError-like
    resp = getattr(exc, "resp", None)
    status2 = getattr(resp, "status", None)
    return isinstance(status2, int) and should_retry_status(status2)
