"""Service dependency messaging (mocked import failure)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from googlekit.core.exceptions import MissingExtraError
from googlekit.core.optional import require_extra


@pytest.mark.parametrize(
    "extra",
    ["gdrive", "gsheets", "gcalendar", "gdocs", "gslides"],
)
def test_missing_client_message_contains_uv_add(extra: str) -> None:
    with (
        patch(
            "googlekit.core.optional.import_module",
            side_effect=ImportError("simulated missing clients"),
        ),
        pytest.raises(MissingExtraError) as exc_info,
    ):
        require_extra(extra)
    message = str(exc_info.value)
    assert "requires Google client libraries" in message
    assert "uv add googlekit" in message


def test_require_extra_succeeds_when_module_present() -> None:
    try:
        require_extra("gdrive")
    except MissingExtraError:
        pytest.skip("google API client not installed in this environment")
