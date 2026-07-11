"""Create a Google Slides presentation with a title slide and text box.

Requires:
    uv add googlekit
"""

from __future__ import annotations

from googlekit.gslides import PredefinedLayout, ShapeType, SlidesClient, TextStyle


def main() -> None:
    slides = SlidesClient.from_oauth("client_secrets.json", token_path="token_slides.json")

    presentation = slides.presentations.create("GoogleKit Demo Deck")
    print(f"Created presentation: {presentation.id}")

    # New presentations include a blank first slide; add a title layout slide.
    add = slides.pages.add(
        presentation.id,
        layout=PredefinedLayout.TITLE_AND_BODY,
        insertion_index=1,
        object_id="slide_title",
    )
    print(f"Added slide replies: {add.replies}")

    slide_ids = slides.pages.get_ids(presentation.id)
    page_id = slide_ids[-1]

    shape = slides.elements.create_shape(
        presentation.id,
        page_id,
        ShapeType.TEXT_BOX,
        object_id="intro_box",
        width_pt=400,
        height_pt=80,
        x_pt=60,
        y_pt=120,
    )
    print(f"Created shape: {shape.replies}")

    slides.text.insert(presentation.id, "intro_box", "Built with GoogleKit")
    slides.text.style(
        presentation.id,
        "intro_box",
        TextStyle(bold=True, font_size_pt=24),
    )

    print(f"Open: https://docs.google.com/presentation/d/{presentation.id}/edit")


if __name__ == "__main__":
    main()
