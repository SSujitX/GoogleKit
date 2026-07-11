"""Service account quickstart (placeholder paths — no real secrets)."""

from __future__ import annotations

from googlekit import GoogleKit

# JSON key from Google Cloud Console. Share target files with the SA email.
CREDENTIALS_FILE = "service-account.json"
# Optional Workspace user for domain-wide delegation (admin-configured).
SUBJECT = None  # e.g. "user@example.com"


def main() -> None:
    kit = GoogleKit.from_service_account(
        credentials_file=CREDENTIALS_FILE,
        subject=SUBJECT,
        services=["gsheets"],
    )
    print("Authenticated scopes:", sorted(kit.scopes.values))
    print(
        "Ordinary service accounts need resources shared with them "
        "unless Workspace domain-wide delegation is configured."
    )


if __name__ == "__main__":
    main()
