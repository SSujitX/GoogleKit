"""Application Default Credentials quickstart."""

from __future__ import annotations

from googlekit import GoogleKit

# Prerequisites (pick one):
#   gcloud auth application-default login
#   set GOOGLE_APPLICATION_CREDENTIALS to a key file path
QUOTA_PROJECT_ID = None  # optional billing/quota project


def main() -> None:
    kit = GoogleKit.from_adc(
        quota_project_id=QUOTA_PROJECT_ID,
        services=["gcalendar"],
    )
    print("Authenticated scopes:", sorted(kit.scopes.values))
    print("ADC client ready")


if __name__ == "__main__":
    main()
