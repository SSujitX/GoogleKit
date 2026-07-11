"""Live Slides API integration (skipped unless explicitly enabled)."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.integration

# Required environment (never commit credentials):
#   GOOGLEKIT_RUN_INTEGRATION=1
#   GOOGLEKIT_CLIENT_SECRETS or GOOGLE_APPLICATION_CREDENTIALS
# Optional:
#   GOOGLEKIT_TEST_PRESENTATION_ID=...


def test_slides_integration_placeholder() -> None:
    if os.environ.get("GOOGLEKIT_RUN_INTEGRATION") != "1":
        pytest.skip(
            "Set GOOGLEKIT_RUN_INTEGRATION=1 and credential env vars to run live Slides tests"
        )
    pytest.fail("Slides integration tests not implemented yet")
