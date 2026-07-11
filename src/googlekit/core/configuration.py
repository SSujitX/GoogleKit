"""Client configuration."""

from __future__ import annotations

from dataclasses import dataclass, field

from googlekit.core.constants import DEFAULT_CHUNK_SIZE, USER_AGENT
from googlekit.core.retries import RetryPolicy


@dataclass(slots=True)
class ClientConfig:
    """Runtime configuration shared by GoogleKit clients."""

    user_agent: str = USER_AGENT
    timeout: float | None = 120.0
    chunk_size: int = DEFAULT_CHUNK_SIZE
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    supports_all_drives: bool = True
    default_timezone: str | None = None

    def with_retries_disabled(self) -> ClientConfig:
        """Return a copy with retries turned off."""
        return ClientConfig(
            user_agent=self.user_agent,
            timeout=self.timeout,
            chunk_size=self.chunk_size,
            retry=RetryPolicy(enabled=False, max_attempts=1),
            supports_all_drives=self.supports_all_drives,
            default_timezone=self.default_timezone,
        )
