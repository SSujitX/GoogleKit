"""Live Drive API integration (skipped unless explicitly enabled)."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.integration

# Required environment (never commit credentials):
#   GOOGLEKIT_RUN_INTEGRATION=1
#   GOOGLEKIT_CLIENT_SECRETS=/path/to/client_secret.json
#   or GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa.json
# Optional:
#   GOOGLEKIT_TOKEN_PATH=/path/to/token.json
#   GOOGLEKIT_TEST_FOLDER_ID=...


def test_drive_integration_placeholder() -> None:
    if os.environ.get("GOOGLEKIT_RUN_INTEGRATION") != "1":
        pytest.skip(
            "Set GOOGLEKIT_RUN_INTEGRATION=1 and credential env vars "
            "(GOOGLEKIT_CLIENT_SECRETS or GOOGLE_APPLICATION_CREDENTIALS) "
            "to run live Drive tests"
        )
    pytest.fail("Drive integration tests not implemented yet")
