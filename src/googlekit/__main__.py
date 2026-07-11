"""Minimal stdlib CLI: version, doctor, auth status."""

from __future__ import annotations

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="googlekit", description="GoogleKit CLI")
    parser.add_argument("--version", action="store_true", help="Print package version")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("doctor", help="Check environment and installed extras")
    auth = sub.add_parser("auth", help="Authentication helpers")
    auth_sub = auth.add_subparsers(dest="auth_command")
    auth_sub.add_parser("status", help="Show non-secret auth status")

    args = parser.parse_args(argv)

    if args.version or args.command is None:
        try:
            ver = version("googlekit")
        except PackageNotFoundError:
            ver = "0.1.0"
        print(f"googlekit {ver}")
        if args.command is None and not args.version:
            parser.print_help()
        return 0

    if args.command == "doctor":
        return _doctor()
    if args.command == "auth" and args.auth_command == "status":
        return _auth_status()

    parser.print_help()
    return 1


def _doctor() -> int:
    from googlekit.auth.credentials import auto_detect_credentials_file
    from googlekit.auth.token_store import default_token_path
    from googlekit.core.optional import installed_extras

    print(f"Python: {sys.version.split()[0]}")
    extras = installed_extras()
    for name, ok in extras.items():
        print(f"Extra {name}: {'installed' if ok else 'missing'}")

    path, is_sa = auto_detect_credentials_file()
    if path:
        kind = "service_account" if is_sa else "oauth_client"
        print(f"Detected credentials file: {path.name} ({kind})")
    else:
        print("Detected credentials file: none")

    token = default_token_path()
    print(f"Default token path: {token}")
    print(f"Token file present: {token.exists()}")
    print("Secrets are never printed by doctor.")
    return 0


def _auth_status() -> int:
    from googlekit.auth.credentials import auto_detect_credentials_file
    from googlekit.auth.token_store import default_token_path
    from googlekit.core.optional import installed_extras

    extras = installed_extras()
    any_google = any(extras.values())
    print(f"Google client libraries: {'yes' if any_google else 'no'}")
    path, is_sa = auto_detect_credentials_file()
    print(f"Local credentials: {'yes' if path else 'no'}")
    if path:
        print(f"Credential type: {'service_account' if is_sa else 'oauth'}")
    print(f"Cached token: {'yes' if default_token_path().exists() else 'no'}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
