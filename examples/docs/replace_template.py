"""Replace template placeholders in a Google Doc.

Create a Doc containing tokens like {{name}} and {{date}}, then run this script.

Requires:
    uv add "googlekit[gdocs]"
"""

from __future__ import annotations

import sys

from googlekit.gdocs import DocsClient


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python replace_template.py <document_id>")
        raise SystemExit(2)

    document_id = sys.argv[1]
    docs = DocsClient.from_oauth("client_secrets.json", token_path="token_docs.json")

    result = docs.content.replace_placeholders(
        document_id,
        {
            "{{name}}": "Ada Lovelace",
            "{{date}}": "2026-07-11",
            "{{role}}": "Analyst",
        },
    )
    print(f"Applied {len(result.replies)} replacement request(s) to {result.document_id}")
    print(f"Open: https://docs.google.com/document/d/{document_id}/edit")


if __name__ == "__main__":
    main()
