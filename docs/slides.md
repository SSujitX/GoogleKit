# Google Slides

Install: `uv add googlekit`

Enable the **Google Slides API**. Export/share may need Drive.

## Client

```python
from googlekit import GoogleKit

kit = GoogleKit.from_oauth("client_secret.json", services=["gslides"])
slides = kit.slides
```

## Managers

| Manager | Role |
| ------- | ---- |
| `slides.presentations` | Create, get, batchUpdate |
| `slides.pages` | Add/delete/duplicate/reorder slides |
| `slides.elements` | Shapes, move/resize, group |
| `slides.text` | Insert/replace/style text, placeholders |
| `slides.images` | Insert/replace/position images |
| `slides.tables` | Create tables, write cells |

## Intended API

```python
deck = slides.presentations.create("Pitch Deck")
slides.presentations.get(deck.id)
slides.pages.add_slide(deck.id, layout="BLANK")
slides.text.replace_all(deck.id, "{{TITLE}}", "Q3 Plan")
slides.images.insert(deck.id, page_id, url="https://example.com/logo.png", ...)
```

Use stable object IDs where the API provides them. Validate dimensions/units before requests.

## Cross-service

Export and sharing go through Drive helpers and require Drive API enablement plus scopes.
