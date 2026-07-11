"""Replace template placeholders across a Google Slides deck.

Put tokens like {{title}} and {{speaker}} in the presentation, then run:

    python replace_template.py <presentation_id>

Requires:
    uv add "googlekit[gslides]"
"""

from __future__ import annotations

import sys

from googlekit.gslides import SlidesClient


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python replace_template.py <presentation_id>")
        raise SystemExit(2)

    presentation_id = sys.argv[1]
    slides = SlidesClient.from_oauth("client_secrets.json", token_path="token_slides.json")

    result = slides.text.replace_placeholders(
        presentation_id,
        {
            "{{title}}": "Q3 Business Review",
            "{{speaker}}": "Ada Lovelace",
            "{{date}}": "2026-07-11",
        },
    )
    print(f"Applied {len(result.replies)} replacement request(s) to {result.presentation_id}")
    print(f"Open: https://docs.google.com/presentation/d/{presentation_id}/edit")


if __name__ == "__main__":
    main()
