"""Service extras messaging (mocked import failure even when extras are installed)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from googlekit.core.exceptions import MissingExtraError
from googlekit.core.optional import require_extra


@pytest.mark.parametrize(
    "extra",
    ["gdrive", "gsheets", "gcalendar", "gdocs", "gslides"],
)
def test_missing_extra_message_contains_uv_add(extra: str) -> None:
    with (
        patch(
            "googlekit.core.optional.import_module",
            side_effect=ImportError("simulated missing extra"),
        ),
        pytest.raises(MissingExtraError) as exc_info,
    ):
        require_extra(extra)
    message = str(exc_info.value)
    assert "support is not installed" in message
    assert f'uv add "googlekit[{extra}]"' in message


def test_require_extra_succeeds_when_module_present() -> None:
    # With --all-extras synced in CI/dev, discovery should import.
    # If not installed, skip rather than fail the conceptual contract test above.
    try:
        require_extra("gdrive")
    except MissingExtraError:
        pytest.skip("google API client not installed in this environment")
