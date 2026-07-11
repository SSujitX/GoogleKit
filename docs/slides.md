# Google Slides

Install: `uv add googlekit`

Enable the **Google Slides API** in Google Cloud Console. Export and sharing go through the Drive API — install the `gdrive` extra and request Drive scopes yourself; GoogleKit never adds them silently.

## Client

```python
from googlekit import GoogleKit
# or: from googlekit.gslides import SlidesClient

client = GoogleKit.from_oauth("client_secret.json", services=["gslides"])
slides = client.slides
```

Standalone:

```python
from googlekit.gslides import SlidesClient

slides = SlidesClient.from_oauth("client_secrets.json", token_path="token_slides.json")
# slides = SlidesClient.from_service_account("sa.json", subject="user@example.com")
# slides = SlidesClient.from_adc(quota_project_id="my-project")
```

Default scopes use `ScopeProfile.READWRITE` → `https://www.googleapis.com/auth/presentations`. Use `ScopeProfile.READONLY` for presentations.readonly, or pass an explicit `ScopeSet`.

### Managers

| Manager | Role |
| ------- | ---- |
| `slides.presentations` | Create, get, raw `batchUpdate`, export, share |
| `slides.pages` | Add / delete / duplicate / reorder slides; list IDs; get page |
| `slides.elements` | Create shapes, move, resize, transform, group / ungroup |
| `slides.text` | Insert / delete / replace / style text and paragraphs |
| `slides.images` | Insert, replace, position/size images |
| `slides.tables` | Create tables, write cells, insert/delete rows/cols, format cells |

---

## Units: EMU and points

Slides sizes and transforms use **English Metric Units (EMU)**.

| Constant | Value |
| -------- | ----- |
| `EMU_PER_PT` | **12700** (1 point = 12700 EMUs) |
| `EMU_PER_INCH` | 914400 |

```python
from googlekit.gslides import Size, AffineTransform, pt_to_emu, inches_to_emu
from googlekit.gslides.models import EMU_PER_PT

assert EMU_PER_PT == 12700
pt_to_emu(72)           # 914400  (one inch)
Size.from_pt(300, 100)  # width/height in EMUs
Size.from_inches(5, 3)
AffineTransform.translate_pt(50, 80)
```

Helpers accept convenient `*_pt` kwargs and convert internally. Prefer those unless you need an explicit `Size` / `AffineTransform`.

---

## Layouts (`PredefinedLayout`)

When adding slides, pass a `PredefinedLayout` (or matching string):

| Layout | Typical use |
| ------ | ----------- |
| `BLANK` | Empty canvas (default for `pages.add`) |
| `TITLE` | Title slide |
| `TITLE_AND_BODY` | Title + body |
| `TITLE_AND_TWO_COLUMNS` | Title + two columns |
| `TITLE_ONLY` | Title only |
| `SECTION_HEADER` | Section divider |
| `SECTION_TITLE_AND_DESCRIPTION` | Section title + description |
| `ONE_COLUMN_TEXT` | Single text column |
| `MAIN_POINT` | Main point |
| `BIG_NUMBER` | Large number callout |
| `CAPTION_ONLY` | Caption only |

```python
from googlekit.gslides import PredefinedLayout

slides.pages.add(presentation_id, layout=PredefinedLayout.TITLE_AND_BODY)
```

---

## Presentations (`slides.presentations`)

### `create(title="Untitled presentation") → Presentation`

```python
presentation = slides.presentations.create("Pitch Deck")
print(presentation.id, presentation.title, presentation.revision_id)
print(presentation.slide_ids())   # ordered slide object IDs
print(presentation.page_size)     # Size in EMUs when present
```

New presentations include an initial slide.

### `get(presentation_id) → Presentation`

```python
presentation = slides.presentations.get(presentation_id)
for slide in presentation.slides:
    print(slide.object_id, len(slide.elements))
    for el in slide.elements:
        print(" ", el.object_id, el.kind, el.size, el.transform)
# element kinds: shape | image | table | line | video | sheetsChart | wordArt | group | …
```

### `batch_update(presentation_id, requests, *, write_control=None) → BatchUpdateResult`

```python
result = slides.presentations.batch_update(
    presentation_id,
    [{"createSlide": {"slideLayoutReference": {"predefinedLayout": "BLANK"}}}],
    write_control={"requiredRevisionId": presentation.revision_id},
)
print(result.presentation_id, result.replies)
```

### `export(presentation_id, export_format, destination=None)`

Exports via Drive. Requires the `gdrive` extra and a Drive scope (`drive`, `drive.readonly`, or `drive.file`). Scopes are **not** added automatically.

```python
slides.presentations.export(presentation_id, "pdf", destination="deck.pdf")
slides.presentations.export(presentation_id, "pptx")  # bytes when destination omitted
```

### `share(presentation_id, *, email=None, role="reader", type="user", domain=None, send_notification=False)`

Requires `gdrive` and a Drive write scope (`drive` or `drive.file`).

```python
slides.presentations.share(
    presentation_id,
    email="reviewer@example.com",
    role="commenter",
    send_notification=True,
)
```

Authorize with Drive when needed:

```python
from googlekit.auth.scopes import Scope, ScopeSet
from googlekit.gslides import SlidesClient

slides = SlidesClient.from_oauth(
    "client_secrets.json",
    scopes=ScopeSet.of(Scope.PRESENTATIONS, Scope.DRIVE_FILE),
)
```

---

## Pages (`slides.pages`)

### `add(presentation_id, *, layout=BLANK, insertion_index=None, object_id=None)`

```python
from googlekit.gslides import PredefinedLayout

result = slides.pages.add(
    presentation_id,
    layout=PredefinedLayout.TITLE_AND_BODY,
    insertion_index=1,
    object_id="slide_title",
)
# createSlide reply includes the new objectId when not supplied
```

### `delete(presentation_id, slide_object_id)`

```python
slides.pages.delete(presentation_id, "slide_title")
```

### `duplicate(presentation_id, slide_object_id, *, object_ids=None)`

```python
slides.pages.duplicate(presentation_id, "slide_title")
slides.pages.duplicate(
    presentation_id,
    "slide_title",
    object_ids={"slide_title": "slide_title_copy"},
)
```

### `reorder(presentation_id, slide_object_ids, insertion_index)`

Moves the listed slides (order preserved) to a zero-based insertion index.

```python
ids = slides.pages.get_ids(presentation_id)
slides.pages.reorder(presentation_id, [ids[-1]], insertion_index=0)
```

### `get_ids(presentation_id) → list[str]`

```python
slide_ids = slides.pages.get_ids(presentation_id)
```

### `get_page(presentation_id, page_object_id) → dict`

Fetches a raw page resource (slide, layout, master, or notes).

```python
page = slides.pages.get_page(presentation_id, slide_ids[0])
```

### `list_slides(presentation_id) → Presentation`

Convenience wrapper around `presentations.get`.

```python
deck = slides.pages.list_slides(presentation_id)
```

---

## Elements (`slides.elements`)

### `create_shape(presentation_id, page_object_id, shape_type=TEXT_BOX, …)`

```python
from googlekit.gslides import ShapeType, Size, AffineTransform

slides.elements.create_shape(
    presentation_id,
    page_id,
    ShapeType.TEXT_BOX,
    object_id="intro_box",
    width_pt=400,
    height_pt=80,
    x_pt=60,
    y_pt=120,
)

# Or explicit EMU size / transform:
slides.elements.create_shape(
    presentation_id,
    page_id,
    ShapeType.RECTANGLE,
    size=Size.from_pt(200, 100),
    transform=AffineTransform.translate_pt(40, 40),
)
# ShapeType: TEXT_BOX, RECTANGLE, ROUND_RECTANGLE, ELLIPSE, TRIANGLE, …
```

### `delete(presentation_id, object_id)`

```python
slides.elements.delete(presentation_id, "intro_box")
```

### `move` — preserves scale

`move` sets translation in points but **keeps the current scale/shear** from the element. Absolute updates that reset scale to `1` would shrink/inflate already-sized objects.

```python
slides.elements.move(presentation_id, "intro_box", x_pt=100, y_pt=150)
# apply_mode defaults to "ABSOLUTE"
```

### `resize` — scale from current size

Create paths set full EMU size with `scaleX/Y = 1`. Resize therefore sets:

`scale = target_emu / current_size_emu`

(not raw EMU magnitudes, which would inflate by ~12700×).

```python
slides.elements.resize(
    presentation_id,
    "intro_box",
    width_pt=500,
    height_pt=100,
    x_pt=60,   # optional; omit to keep current translation
    y_pt=120,
)
```

### `set_transform(presentation_id, object_id, transform, *, apply_mode="ABSOLUTE")`

```python
slides.elements.set_transform(
    presentation_id,
    "intro_box",
    AffineTransform(scale_x=1.5, scale_y=1.5, translate_x_emu=pt_to_emu(50), translate_y_emu=pt_to_emu(50)),
)
```

### `group` / `ungroup`

```python
slides.elements.group(presentation_id, ["shape_a", "shape_b"], group_object_id="grp1")
slides.elements.ungroup(presentation_id, ["grp1"])
```

---

## Text (`slides.text`)

Text lives on shapes (and table cells via the tables manager). Use the shape/table **object ID**.

### `insert(presentation_id, object_id, text, *, insertion_index=0)`

```python
slides.text.insert(presentation_id, "intro_box", "Built with GoogleKit")
slides.text.insert(presentation_id, "intro_box", " — v1", insertion_index=18)
```

### `delete(presentation_id, object_id, *, start_index=0, end_index=None)`

Omit `end_index` to delete **all** text (`textRange.type = ALL`).

```python
slides.text.delete(presentation_id, "intro_box")
slides.text.delete(presentation_id, "intro_box", start_index=0, end_index=5)
```

### `replace_all` / `replace_placeholders`

```python
slides.text.replace_all(presentation_id, "{{TITLE}}", "Q3 Plan")
slides.text.replace_all(
    presentation_id,
    "draft",
    "final",
    match_case=False,
    page_object_ids=[slide_ids[0]],
)

slides.text.replace_placeholders(
    presentation_id,
    {
        "{{title}}": "Q3 Business Review",
        "{{speaker}}": "Ada Lovelace",
        "{{date}}": "2026-07-12",
    },
)
```

### `style` / `style_paragraph`

```python
from googlekit.gslides import TextStyle, ParagraphStyle

slides.text.style(
    presentation_id,
    "intro_box",
    TextStyle(bold=True, font_size_pt=24, font_family="Arial"),
)
# omit end_index → ALL; or pass start_index/end_index for FIXED_RANGE

slides.text.style_paragraph(
    presentation_id,
    "intro_box",
    ParagraphStyle(alignment="CENTER", line_spacing=100, space_below_pt=8),
)
```

Foreground colors use Slides color objects, e.g.:

```python
TextStyle(
    foreground_color={
        "opaqueColor": {"rgbColor": {"red": 0.1, "green": 0.1, "blue": 0.1}}
    }
)
```

---

## Images (`slides.images`)

### `insert_url(presentation_id, page_object_id, url, …)`

Public HTTPS URL required.

```python
slides.images.insert_url(
    presentation_id,
    page_id,
    "https://example.com/logo.png",
    object_id="logo",
    width_pt=160,
    height_pt=60,
    x_pt=40,
    y_pt=20,
)
```

### `replace(presentation_id, image_object_id, url, *, image_replace_method="CENTER_INSIDE")`

```python
slides.images.replace(presentation_id, "logo", "https://example.com/logo-v2.png")
```

### `position_and_size` — same scale math as resize

Computes `scale = target_emu / current_size_emu` so it matches create paths that store full size with scale 1.

```python
slides.images.position_and_size(
    presentation_id,
    "logo",
    x_pt=80,
    y_pt=40,
    width_pt=200,
    height_pt=75,
)
```

---

## Tables (`slides.tables`)

### `create(presentation_id, page_object_id, rows, columns, …)`

```python
result = slides.tables.create(
    presentation_id,
    page_id,
    rows=3,
    columns=2,
    object_id="metrics",
    width_pt=400,
    height_pt=180,
    x_pt=50,
    y_pt=100,
)
```

### `write_cell` — uses `cellLocation`, not fake cell IDs

Slides table text APIs require the **table `objectId`** plus **`cellLocation`** (`rowIndex` / `columnIndex`). Do not invent per-cell object IDs.

```python
from googlekit.gslides import TextStyle

slides.tables.write_cell(
    presentation_id,
    "metrics",          # table object ID
    row_index=0,
    column_index=0,
    text="Revenue",
    style=TextStyle(bold=True, font_size_pt=14),
)
# Implementation: deleteText ALL in that cell, then insertText at insertionIndex 0
```

### Rows and columns

```python
slides.tables.insert_rows(
    presentation_id, "metrics", number=1, insert_below=True, row_index=0
)
slides.tables.insert_columns(
    presentation_id, "metrics", number=1, insert_right=True, column_index=0
)
slides.tables.delete_row(presentation_id, "metrics", row_index=2)
slides.tables.delete_column(presentation_id, "metrics", column_index=1)
```

### `format_cells` (background)

```python
slides.tables.format_cells(
    presentation_id,
    "metrics",
    row_index=0,
    column_index=0,
    row_span=1,
    column_span=2,
    background_color={"rgbColor": {"red": 0.2, "green": 0.3, "blue": 0.5}},
)
```

---

## Models

Import from `googlekit.gslides`:

| Type | Purpose |
| ---- | ------- |
| `Presentation` | `id`, `title`, `slides`, `page_size`, `revision_id`, `slide_ids()` |
| `SlidePage` | `object_id`, `layout_object_id`, `elements` |
| `PageElement` | `object_id`, `size`, `transform`, `kind` |
| `Size` / `AffineTransform` | EMU geometry |
| `TextStyle` / `ParagraphStyle` | Style field subsets |
| `PredefinedLayout` / `ShapeType` | Enums for layouts and shapes |
| `BatchUpdateResult` | `presentation_id`, `replies`, `write_control` |
| `pt_to_emu` / `inches_to_emu` | Unit helpers (`EMU_PER_PT = 12700`) |

---

## Recipes

### Create a deck with a text box

```python
from googlekit.gslides import PredefinedLayout, ShapeType, SlidesClient, TextStyle

slides = SlidesClient.from_oauth("client_secrets.json", token_path="token_slides.json")
presentation = slides.presentations.create("GoogleKit Demo Deck")

slides.pages.add(
    presentation.id,
    layout=PredefinedLayout.TITLE_AND_BODY,
    insertion_index=1,
    object_id="slide_title",
)

page_id = slides.pages.get_ids(presentation.id)[-1]

slides.elements.create_shape(
    presentation.id,
    page_id,
    ShapeType.TEXT_BOX,
    object_id="intro_box",
    width_pt=400,
    height_pt=80,
    x_pt=60,
    y_pt=120,
)
slides.text.insert(presentation.id, "intro_box", "Built with GoogleKit")
slides.text.style(presentation.id, "intro_box", TextStyle(bold=True, font_size_pt=24))
```

### Fill a template deck

```python
slides.text.replace_placeholders(
    presentation_id,
    {
        "{{title}}": "Q3 Business Review",
        "{{speaker}}": "Ada Lovelace",
        "{{date}}": "2026-07-12",
    },
)
```

### Table with header cells

```python
slides.tables.create(
    presentation_id, page_id, rows=2, columns=2, object_id="grid", width_pt=480, height_pt=160
)
slides.tables.write_cell(presentation_id, "grid", 0, 0, "Metric")
slides.tables.write_cell(presentation_id, "grid", 0, 1, "Value")
slides.tables.write_cell(presentation_id, "grid", 1, 0, "ARR")
slides.tables.write_cell(presentation_id, "grid", 1, 1, "$1.2M")
slides.tables.format_cells(
    presentation_id,
    "grid",
    row_index=0,
    column_index=0,
    column_span=2,
    background_color={"rgbColor": {"red": 0.15, "green": 0.25, "blue": 0.45}},
)
```

### Move and resize without destroying scale

```python
# After create_shape / insert_url (size stored in EMU, scale ≈ 1):
slides.elements.move(presentation_id, "intro_box", x_pt=80, y_pt=140)
slides.elements.resize(presentation_id, "intro_box", width_pt=450, height_pt=90)
slides.images.position_and_size(
    presentation_id, "logo", x_pt=40, y_pt=20, width_pt=180, height_pt=70
)
```

### Export PDF and share (Drive scopes required)

```python
from googlekit.auth.scopes import Scope, ScopeSet
from googlekit.gslides import SlidesClient

slides = SlidesClient.from_oauth(
    "client_secrets.json",
    scopes=ScopeSet.of(Scope.PRESENTATIONS, Scope.DRIVE_FILE),
)

slides.presentations.export(presentation_id, "pdf", destination="deck.pdf")
slides.presentations.share(presentation_id, email="peer@example.com", role="writer")
```

### Reorder and duplicate slides

```python
ids = slides.pages.get_ids(presentation_id)
slides.pages.duplicate(presentation_id, ids[0])
slides.pages.reorder(presentation_id, [ids[-1]], insertion_index=0)
```

---

## Cross-service notes

- Presentation IDs are Drive file IDs.
- Service accounts need the presentation shared with them (or domain-wide delegation).
- Prefer `drive.file` when export/share should stay limited to files the app creates/opens.
- See [scopes](scopes.md) and [Drive](drive.md).
