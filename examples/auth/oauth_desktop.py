"""OAuth desktop quickstart (placeholder paths — no real secrets)."""

from __future__ import annotations

from googlekit import GoogleKit

# Download OAuth client secrets from Google Cloud Console (Desktop app).
CLIENT_SECRETS = "client_secret.json"
TOKEN_PATH = "token.json"


def main() -> None:
    kit = GoogleKit.from_oauth(
        client_secrets=CLIENT_SECRETS,
        token_path=TOKEN_PATH,
        services=["gdrive"],
    )
    # First run opens a browser for consent; later runs refresh the cached token.
    print("Authenticated scopes:", sorted(kit.scopes.values))
    print("Drive client ready:", kit.drive is not None)


if __name__ == "__main__":
    main()
