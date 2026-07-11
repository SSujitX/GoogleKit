"""ClientConfig unit tests."""

from __future__ import annotations

import pytest

from googlekit import ClientConfig, RetryPolicy
from googlekit.core.exceptions import ValidationError
from googlekit.core.retries import RetryPolicy as RetryPolicyCore


def test_client_config_and_retry_policy_exported_from_googlekit() -> None:
    assert ClientConfig is not None
    assert RetryPolicy is RetryPolicyCore


def test_client_config_retry_int_shorthand() -> None:
    config = ClientConfig(retry=5)
    assert isinstance(config.retry, RetryPolicy)
    assert config.retry.max_attempts == 5
    assert config.retry.enabled is True


def test_client_config_retry_policy_passthrough() -> None:
    policy = RetryPolicy(max_attempts=8, initial_delay=1.0, jitter=0.0)
    config = ClientConfig(retry=policy)
    assert config.retry is policy


def test_client_config_retry_shorthand_rejects_zero() -> None:
    with pytest.raises(ValidationError, match=">= 1"):
        ClientConfig(retry=0)


def test_with_retries_disabled() -> None:
    config = ClientConfig(retry=5).with_retries_disabled()
    assert config.retry.enabled is False
    assert config.retry.max_attempts == 1
