---
title: Google Docs API Python client (GoogleKit)
description: >-
  Create and edit Google Docs with GoogleKit — insert text, tables, batch updates,
  UTF-16-safe indexes, and Drive export/share for Docs API v1.
---

# Google Docs

Install: `uv add googlekit`

Enable the **Google Docs API** in Google Cloud Console. Export and sharing go through the Drive API — request Drive scopes yourself when needed; GoogleKit never adds them silently.

**Official Google docs:** [Docs API guides](https://developers.google.com/workspace/docs/api/how-tos/overview) ·
[REST reference](https://developers.google.com/workspace/docs/api/reference/rest) ·
[documents](https://developers.google.com/workspace/docs/api/reference/rest/v1/documents) ·
[Structure](https://developers.google.com/workspace/docs/api/concepts/structure) ·
[Enable API](https://console.cloud.google.com/apis/library/docs.googleapis.com)

## Client

```python
from googlekit import GoogleKit
# or: from googlekit.gdocs import DocsClient

client = GoogleKit.from_oauth("client_secret.json", services=["gdocs"])
docs = client.docs
```

Standalone:

```python
from googlekit.gdocs import DocsClient

docs = DocsClient.from_oauth("client_secrets.json", token_path="token_docs.json")
# docs = DocsClient.from_service_account("sa.json", subject="user@example.com")
# docs = DocsClient.from_adc(quota_project_id="my-project")
```

Default scopes use `ScopeProfile.READWRITE` → `https://www.googleapis.com/auth/documents`. Pass `profile=ScopeProfile.READONLY` for documents.readonly, or supply an explicit `ScopeSet`.

### Managers

| Manager | Role |
| ------- | ---- |
| `docs.documents` | Create, get, inspect structure, raw `batchUpdate`, export, share |
| `docs.content` | Insert/append/replace/delete text, styles, headings, lists, links, named ranges |
| `docs.tables` | Insert tables, rows/columns, write cells, format cells |
| `docs.images` | Insert, resize, replace inline images from public URLs |

### Optional shortcuts vs managers

Both appear after `docs.` (typed as `DocsAPI`).

| Shortcut | Delegates to |
| -------- | ------------ |
| `create_document(title)` | `documents.create(title)` |
| `get_document(id, ...)` | `documents.get(id, ...)` |
| `append_text(id, text)` | `content.append_text(id, text)` |
| `insert_text(id, text, index, ...)` | `content.insert_text(...)` |

```python
# Manager
doc = docs.documents.create("Proposal")
docs.content.append_text(doc.id, "Hello\n")
docs.content.insert_text(doc.id, "Title\n", index=1)

# Shortcut (equivalent)
doc = docs.create_document("Proposal")
docs.append_text(doc.id, "Hello\n")
docs.insert_text(doc.id, "Title\n", index=1)
```

---

## Critical: UTF-16 indexes

The Docs API measures **every** `location.index`, `startIndex`, and `endIndex` in **UTF-16 code units**, not Python `str` indexes and not UTF-8 bytes.

- BMP characters (most Latin, many CJK) = **1** UTF-16 unit
- Non-BMP characters (many emoji, some rare ideographs) = **2** units (surrogate pair)

```python
from googlekit.gdocs.utf16 import utf16_len, offset_utf16, py_index_to_utf16

text = "Hi 😄"
len(text)        # 4  (Python code points)
utf16_len(text)  # 5  (Docs index units)
```

Body content in a new document typically starts at UTF-16 index **1** (index `0` is the segment start). Always use the helpers when computing ranges after insert:

```python
from googlekit.gdocs.utf16 import (
    offset_utf16,
    py_index_to_utf16,
    py_slice_to_utf16_range,
    utf16_index_to_py,
    utf16_len,
    utf16_range_to_py_slice,
)

title = "Welcome\n"
docs.content.insert_text(document_id, title, index=1)
end = offset_utf16(1, title)  # 1 + utf16_len(title)
```

`ContentManager.text_utf16_length(text)` is the same as `utf16_len(text)`.

!!! warning "Emoji and indexes"
    If you compute ranges with `len()` or Python slices and the document contains emoji, styling and deletes will land on the wrong characters. Convert with `py_index_to_utf16` / `offset_utf16` first.

---

## Multi-tab documents (`tab_id`)

Newer Docs can have multiple tabs. Methods that accept a location/range support optional `tab_id` (and `segment_id` for headers/footers/footnotes):

- `docs.content.insert_text(..., tab_id=...)`
- `docs.content.delete_range(..., tab_id=...)`

`TextRange` also carries `tab_id` when building raw `batchUpdate` ranges.

```python
docs.content.insert_text(document_id, "Tab note\n", index=1, tab_id="t.abc123")
docs.content.delete_range(document_id, 1, 10, tab_id="t.abc123")
```

---

## Documents (`docs.documents`)

### `create(title="Untitled document") → Document`

```python
document = docs.documents.create("Proposal")
print(document.id, document.title, document.revision_id)
print(document.body_end_index)   # last structural endIndex
print(document.plain_text)       # concatenated paragraph text
```

### `get(document_id) → Document`

```python
document = docs.documents.get(document_id)
for el in document.structural_elements:
    print(el.kind, el.start_index, el.end_index, el.text)
# kinds: paragraph | table | tableOfContents | sectionBreak | unknown
```

Named ranges from the API are exposed as
`document.named_ranges: dict[str, list[TextRange]]`. With tab content enabled,
GoogleKit reads ranges from every top-level and nested `documentTab`; each
`TextRange.tab_id` identifies its source tab. Individual tab ranges are also
available through `document.tabs[n].named_ranges`.

### `inspect_structure(document_id) → list[StructuralElement]`

```python
elements = docs.documents.inspect_structure(document_id)
tables = [e for e in elements if e.kind == "table"]
```

### `batch_update(document_id, requests, *, write_control=None) → BatchUpdateResult`

Low-level escape hatch. Indexes in `requests` **must** be UTF-16.

```python
result = docs.documents.batch_update(
    document_id,
    [{"insertText": {"location": {"index": 1}, "text": "Hello\n"}}],
    write_control={"requiredRevisionId": document.revision_id},
)
print(result.document_id, result.replies)
```

### `export(document_id, export_format, destination=None)`

Exports via Drive. Requires:

1. `gdrive` extra installed
2. A Drive scope already on the credential: `drive`, `drive.readonly`, or `drive.file`

Scopes are **not** added automatically. Raises `InsufficientScopesError` / `MissingExtraError` otherwise.

```python
# bytes in memory
result = docs.documents.export(document_id, "pdf")

# write to disk
docs.documents.export(document_id, "docx", destination="proposal.docx")
# short names: pdf, docx, txt, … or a full export MIME type
```

Authorize with Drive when you need this:

```python
from googlekit.auth.scopes import Scope, ScopeSet, ScopeProfile

docs = DocsClient.from_oauth(
    "client_secrets.json",
    scopes=ScopeSet.of(Scope.DOCUMENTS, Scope.DRIVE_FILE),
)
```

Or combine services on the facade:

```python
client = GoogleKit.from_oauth(
    "client_secret.json",
    services=["gdocs", "gdrive"],
)
docs = client.docs
```

### `share(document_id, *, email=None, role="reader", type="user", domain=None, send_notification=False)`

Shares via Drive Permissions. Requires `gdrive` extra and a Drive **write** scope (`drive` or `drive.file`).

```python
docs.documents.share(
    document_id,
    email="reviewer@example.com",
    role="commenter",
    type="user",
    send_notification=True,
)

docs.documents.share(document_id, type="domain", domain="example.com", role="reader")
docs.documents.share(document_id, type="anyone", role="reader")
```

---

## Content (`docs.content`)

### `insert_text(document_id, text, index, *, segment_id=None, tab_id=None)`

Insert at a UTF-16 index. Newlines create paragraphs.

```python
docs.content.insert_text(document_id, "Hello world\n", index=1)
docs.content.insert_text(document_id, "Footer note", index=1, segment_id=header_id)
```

### `append_text(document_id, text)`

Appends just before the body's final newline (`body_end_index - 1`).

```python
docs.content.append_text(document_id, "Closing paragraph.\n")
```

### `delete_range(document_id, start_index, end_index, *, segment_id=None, tab_id=None)`

Deletes the half-open UTF-16 range `[start_index, end_index)`.

```python
docs.content.delete_range(document_id, 1, 12)
```

### `replace_all(document_id, find_text, replace_text, *, match_case=True)`

```python
docs.content.replace_all(document_id, "{{NAME}}", "Ada Lovelace")
docs.content.replace_all(document_id, "draft", "final", match_case=False)
```

### `replace_placeholders(document_id, mapping, *, match_case=True)`

One `batchUpdate` with multiple `replaceAllText` requests — ideal for templates.

```python
docs.content.replace_placeholders(
    document_id,
    {
        "{{name}}": "Ada Lovelace",
        "{{date}}": "2026-07-12",
        "{{role}}": "Analyst",
    },
)
```

### `style_text(document_id, start_index, end_index, style, *, segment_id=None)`

```python
from googlekit.gdocs import TextStyle

docs.content.style_text(
    document_id,
    start,
    end,
    TextStyle(
        bold=True,
        italic=True,
        underline=False,
        strikethrough=False,
        font_size_pt=14,
        font_family="Roboto",
        foreground_color={"color": {"rgbColor": {"red": 0.1, "green": 0.2, "blue": 0.6}}},
        background_color={"color": {"rgbColor": {"red": 1, "green": 1, "blue": 0.8}}},
    ),
)
```

### `style_paragraph(document_id, start_index, end_index, style, *, segment_id=None)`

```python
from googlekit.gdocs import ParagraphStyle

docs.content.style_paragraph(
    document_id,
    start,
    end,
    ParagraphStyle(
        alignment="CENTER",
        line_spacing=115,
        space_above_pt=6,
        space_below_pt=6,
        indent_start_pt=18,
        indent_first_line_pt=0,
    ),
)
```

### `set_heading(document_id, start_index, end_index, heading, *, segment_id=None)`

```python
from googlekit.gdocs import NamedStyleType
from googlekit.gdocs.utf16 import offset_utf16

title = "Overview\n"
docs.content.insert_text(document_id, title, index=1)
docs.content.set_heading(
    document_id,
    1,
    offset_utf16(1, title.rstrip("\n")),
    NamedStyleType.HEADING_1,
)
# Also: TITLE, SUBTITLE, HEADING_2 … HEADING_6, NORMAL_TEXT
```

### `insert_page_break(document_id, index, *, segment_id=None)`

```python
docs.content.insert_page_break(document_id, index=doc.body_end_index - 1)
```

### `create_list` / `delete_list`

```python
from googlekit.gdocs import BulletPreset

docs.content.create_list(
    document_id,
    start,
    end,
    preset=BulletPreset.BULLET_DISC_CIRCLE_SQUARE,
)
# NUMBERED_DECIMAL_ALPHA_ROMAN, NUMBERED_DECIMAL_NESTED, BULLET_CHECKBOX, …

docs.content.delete_list(document_id, start, end)
```

### `insert_link(document_id, start_index, end_index, url, *, segment_id=None)`

```python
docs.content.insert_link(document_id, start, end, "https://example.com")
```

### Named ranges

```python
docs.content.create_named_range(document_id, "signature_block", start, end)
docs.content.delete_named_range(document_id, name="signature_block")
docs.content.delete_named_range(document_id, named_range_id="kix.abc")
```

### `insert_styled_text(document_id, text, index, style, *, segment_id=None)`

Inserts text and styles the inserted span in one batch (end index via `offset_utf16`).

```python
docs.content.insert_styled_text(
    document_id,
    "Important\n",
    index=1,
    style=TextStyle(bold=True, font_size_pt=16),
)
```

---

## Tables (`docs.tables`)

Table mutations locate the table by **`table_start_index`** — the UTF-16 start index of the table element from `inspect_structure` / `Document.structural_elements` (not a cell content range).

### `insert_table(document_id, rows, columns, index, *, segment_id=None)`

```python
docs.tables.insert_table(document_id, rows=3, columns=2, index=1)

doc = docs.documents.get(document_id)
table = next(e for e in doc.structural_elements if e.kind == "table")
table_start = table.start_index  # use this for later mutations
```

### Rows and columns

```python
docs.tables.insert_rows(document_id, table_start, row_index=0, insert_below=True, number=1)
docs.tables.delete_row(document_id, table_start, row_index=2)

docs.tables.insert_columns(document_id, table_start, column_index=0, insert_right=True, number=1)
docs.tables.delete_column(document_id, table_start, column_index=1)
```

### `write_cell(document_id, cell_start_index, text, *, style=None)`

Writes at the cell's **content start index** (typically cell start + 1). The caller should delete existing cell content (except the trailing newline) when replacing.

```python
# After inspecting structure / cell indexes:
docs.tables.write_cell(
    document_id,
    cell_start_index=42,
    text="Q1",
    style=TextStyle(bold=True),
)
```

### `format_cell(document_id, table_start_index, *, row_index=0, column_index=0, …)`

Applies `updateTableCellStyle`. Borders use official fields **`borderTop` / `borderBottom` / `borderLeft` / `borderRight`** (not a single `border` field). Colors are Docs `OptionalColor` objects.

```python
bg = {"color": {"rgbColor": {"red": 0.9, "green": 0.9, "blue": 0.95}}}
border = {"color": {"rgbColor": {"red": 0.2, "green": 0.2, "blue": 0.2}}}

docs.tables.format_cell(
    document_id,
    table_start_index=table_start,
    row_index=0,
    column_index=0,
    row_span=1,
    column_span=2,
    background_color=bg,
    border_color=border,
    border_width_pt=1.0,
)
```

---

## Images (`docs.images`)

Images must be reachable at a **public HTTPS URL**.

### `insert_from_url(document_id, url, index, *, width_pt=None, height_pt=None, segment_id=None)`

```python
result = docs.images.insert_from_url(
    document_id,
    "https://example.com/logo.png",
    index=1,
    width_pt=120,
    height_pt=40,
)
# reply may include the new object ID
```

### `resize(document_id, start_index, url, *, width_pt, height_pt, end_index=None)`

Docs has no resize-by-index RPC. This deletes `[start_index, end_index)` (default end = start + 1) and re-inserts the image at the same index with new dimensions.

```python
docs.images.resize(
    document_id,
    start_index=10,
    url="https://example.com/logo.png",
    width_pt=200,
    height_pt=60,
)
```

### `replace(document_id, object_id, url, *, image_replace_method="CENTER_CROP")`

```python
docs.images.replace(document_id, object_id, "https://example.com/new.png")
```

---

## Models

Import from `googlekit.gdocs`:

| Type | Purpose |
| ---- | ------- |
| `Document` | `id`, `title`, `revision_id`, `body_end_index`, `structural_elements`, `named_ranges`, `tabs`, `plain_text` |
| `DocumentTab` | `tab_id`, `title`, `body_end_index`, `structural_elements`, `named_ranges` |
| `StructuralElement` | `kind`, indexes, optional `text`, `raw` |
| `TextRange` | UTF-16 range + optional `segment_id` / `tab_id` |
| `TextStyle` / `ParagraphStyle` | Field subsets for style updates |
| `NamedStyleType` | `HEADING_1` … `TITLE`, `NORMAL_TEXT`, … |
| `BulletPreset` | Bullet / numbered list presets |
| `BatchUpdateResult` | `document_id`, `replies`, `write_control` |

---

## Recipes

### Create a styled document

```python
from googlekit.gdocs import DocsClient, NamedStyleType, TextStyle
from googlekit.gdocs.utf16 import offset_utf16

docs = DocsClient.from_oauth("client_secrets.json", token_path="token_docs.json")
document = docs.documents.create("GoogleKit Demo Document")

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
```

### Fill a template Doc

```python
docs.content.replace_placeholders(
    document_id,
    {"{{name}}": "Ada", "{{date}}": "2026-07-12"},
)
```

### Insert a table and style the header row

```python
docs.tables.insert_table(document_id, rows=2, columns=3, index=1)
doc = docs.documents.get(document_id)
table_start = next(e.start_index for e in doc.structural_elements if e.kind == "table")

docs.tables.format_cell(
    document_id,
    table_start,
    row_index=0,
    column_index=0,
    column_span=3,
    background_color={"color": {"rgbColor": {"red": 0.2, "green": 0.3, "blue": 0.5}}},
)
```

### Export PDF and share (Drive scopes required)

```python
from googlekit.auth.scopes import Scope, ScopeSet
from googlekit.gdocs import DocsClient

docs = DocsClient.from_oauth(
    "client_secrets.json",
    scopes=ScopeSet.of(Scope.DOCUMENTS, Scope.DRIVE_FILE),
)

docs.documents.export(document_id, "pdf", destination="out.pdf")
docs.documents.share(document_id, email="peer@example.com", role="writer")
```

### Raw `batchUpdate` with write control

```python
doc = docs.documents.get(document_id)
docs.documents.batch_update(
    document_id,
    [{"insertText": {"location": {"index": 1}, "text": "Pinned\n"}}],
    write_control={"requiredRevisionId": doc.revision_id},
)
```

---

## Cross-service notes

- Document IDs are Drive file IDs — the same ID works with Drive file APIs.
- Service accounts need the Doc shared with them (or domain-wide delegation).
- Prefer `drive.file` when export/share should stay limited to files the app creates/opens.
- See [scopes](scopes.md) and [Drive](drive.md).
