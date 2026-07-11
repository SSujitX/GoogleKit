"""Live Sheets API integration (skipped unless explicitly enabled)."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.integration

# Required environment (never commit credentials):
#   GOOGLEKIT_RUN_INTEGRATION=1
#   GOOGLEKIT_CLIENT_SECRETS or GOOGLE_APPLICATION_CREDENTIALS
#   GOOGLEKIT_TEST_SPREADSHEET_ID=...


def test_sheets_integration_placeholder() -> None:
    if os.environ.get("GOOGLEKIT_RUN_INTEGRATION") != "1":
        pytest.skip(
            "Set GOOGLEKIT_RUN_INTEGRATION=1, credentials, and "
            "GOOGLEKIT_TEST_SPREADSHEET_ID to run live Sheets tests"
        )
    pytest.fail("Sheets integration tests not implemented yet")
