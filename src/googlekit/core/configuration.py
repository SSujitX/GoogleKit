"""Client configuration."""

from __future__ import annotations

from dataclasses import dataclass, field

from googlekit.core.constants import DEFAULT_CHUNK_SIZE, USER_AGENT
from googlekit.core.exceptions import ValidationError
from googlekit.core.retries import RetryPolicy


@dataclass(slots=True)
class ClientConfig:
    """Runtime settings shared by ``GoogleKit`` and per-service clients.

    Pass into ``GoogleKit.from_oauth(..., config=...)``, ``GoogleKit.auto``, or
    ``DriveClient.from_oauth`` / other service factories.

    Examples::

        from googlekit import ClientConfig, RetryPolicy

        # Most common: more attempts on flaky networks / rate limits
        config = ClientConfig(retry=5)

        # Full control
        config = ClientConfig(retry=RetryPolicy(max_attempts=8, initial_delay=1.0))

        # Calendar: localize naive datetimes
        config = ClientConfig(default_timezone="America/New_York")

        # Disable retries (tests)
        config = ClientConfig().with_retries_disabled()
    """

    user_agent: str = USER_AGENT
    """HTTP ``User-Agent`` sent on Google API requests (default ``googlekit/<version>``)."""

    timeout: float | None = 120.0
    """Request timeout in seconds for the underlying HTTP transport. ``None`` uses library defaults."""

    chunk_size: int = DEFAULT_CHUNK_SIZE
    """Resumable upload/download chunk size in bytes (default 256 KiB)."""

    retry: RetryPolicy | int = field(default_factory=RetryPolicy)
    """Retry policy for transient API/transport failures.

    Pass a :class:`~googlekit.core.retries.RetryPolicy`, or an ``int`` shorthand for
    ``RetryPolicy(max_attempts=N)`` (e.g. ``ClientConfig(retry=5)``).
    """

    supports_all_drives: bool = True
    """When True, Drive calls include Shared Drive parameters (``supportsAllDrives``, etc.)."""

    default_timezone: str | None = None
    """IANA timezone (e.g. ``America/New_York``) used to localize naive Calendar datetimes.

    Required for timed Calendar events/freebusy when callers pass naive ``datetime`` values.
    """

    def __post_init__(self) -> None:
        if isinstance(self.retry, int):
            if self.retry < 1:
                raise ValidationError("retry max_attempts shorthand must be >= 1")
            self.retry = RetryPolicy(max_attempts=self.retry)

    def with_retries_disabled(self) -> ClientConfig:
        """Return a copy with retries turned off (useful in unit tests)."""
        return ClientConfig(
            user_agent=self.user_agent,
            timeout=self.timeout,
            chunk_size=self.chunk_size,
            retry=RetryPolicy(enabled=False, max_attempts=1),
            supports_all_drives=self.supports_all_drives,
            default_timezone=self.default_timezone,
        )
