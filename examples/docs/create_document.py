"""Create a Google Doc and insert styled text.

Requires:
    uv add googlekit

Auth: place client_secrets.json in the working directory or set paths below.
"""

from __future__ import annotations

from googlekit.gdocs import DocsClient, NamedStyleType, TextStyle
from googlekit.gdocs.utf16 import offset_utf16


def main() -> None:
    docs = DocsClient.from_oauth("client_secrets.json", token_path="token_docs.json")

    document = docs.documents.create("GoogleKit Demo Document")
    print(f"Created document: {document.id} — {document.title}")

    # Body content starts at UTF-16 index 1.
    title = "Welcome to GoogleKit\n"
    docs.content.insert_text(document.id, title, index=1)
    docs.content.set_heading(
        document.id,
        1,
        offset_utf16(1, title.rstrip("\n")),
        NamedStyleType.HEADING_1,
    )

    body = "This paragraph was inserted with the Docs API.\n"
    body_start = offset_utf16(1, title)
    docs.content.insert_text(document.id, body, index=body_start)
    docs.content.style_text(
        document.id,
        body_start,
        offset_utf16(body_start, "This paragraph"),
        TextStyle(bold=True, italic=True),
    )

    print(f"Open: https://docs.google.com/document/d/{document.id}/edit")


if __name__ == "__main__":
    main()
