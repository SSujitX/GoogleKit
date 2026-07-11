"""Optional extra loading and MissingExtraError."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from googlekit.core.exceptions import MissingExtraError
from googlekit.core.optional import import_optional, installed_extras, require_extra


def test_require_extra_unknown() -> None:
    with pytest.raises(ValueError, match="Unknown GoogleKit extra"):
        require_extra("gphotos")


def test_missing_extra_error_message() -> None:
    err = MissingExtraError("Google Drive", "gdrive")
    assert "Google Drive support is not installed" in str(err)
    assert 'uv add "googlekit[gdrive]"' in str(err)
    assert err.service == "Google Drive"
    assert err.extra == "gdrive"


def test_require_extra_raises_when_import_fails() -> None:
    with (
        patch(
            "googlekit.core.optional.import_module",
            side_effect=ImportError("no module"),
        ),
        pytest.raises(MissingExtraError) as exc_info,
    ):
        require_extra("gdrive")
    assert 'uv add "googlekit[gdrive]"' in str(exc_info.value)
    assert "Google Drive" in str(exc_info.value)


@pytest.mark.parametrize(
    ("extra", "label"),
    [
        ("gsheets", "Google Sheets"),
        ("gcalendar", "Google Calendar"),
        ("gdocs", "Google Docs"),
        ("gslides", "Google Slides"),
    ],
)
def test_require_extra_message_per_service(extra: str, label: str) -> None:
    with (
        patch(
            "googlekit.core.optional.import_module",
            side_effect=ImportError("missing"),
        ),
        pytest.raises(MissingExtraError) as exc_info,
    ):
        require_extra(extra)
    assert label in str(exc_info.value)
    assert f'uv add "googlekit[{extra}]"' in str(exc_info.value)


def test_import_optional_success() -> None:
    with (
        patch("googlekit.core.optional.require_extra") as req,
        patch(
            "googlekit.core.optional.import_module",
            return_value=object(),
        ) as imp,
    ):
        mod = import_optional("googleapiclient.discovery", extra="gdrive")
    req.assert_called_once_with("gdrive")
    imp.assert_called_once()
    assert mod is not None


def test_installed_extras_mixed() -> None:
    def fake_require(extra: str) -> None:
        if extra == "gdrive":
            return
        raise MissingExtraError("X", extra)

    with patch("googlekit.core.optional.require_extra", side_effect=fake_require):
        status = installed_extras()
    assert status["gdrive"] is True
    assert status["gsheets"] is False
