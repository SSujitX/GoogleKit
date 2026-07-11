---
title: Google Sheets API Python client (GoogleKit)
description: >-
  Read, write, append, and format Google Sheets with GoogleKit. Typed SheetsClient
  for Sheets API v4 — values, worksheets, A1 ranges, and batch updates.
---

# Google Sheets

Install:

```bash
uv add googlekit
```

Enable the **Google Sheets API** in Google Cloud Console. Sharing or Drive-side export also needs the Drive API and scopes.

**Official Google docs:** [Sheets API guides](https://developers.google.com/workspace/sheets/api/guides/concepts) ·
[REST reference](https://developers.google.com/workspace/sheets/api/reference/rest) ·
[Values](https://developers.google.com/workspace/sheets/api/reference/rest/v4/spreadsheets.values) ·
[A1 notation](https://developers.google.com/workspace/sheets/api/guides/concepts#cell) ·
[Enable API](https://console.cloud.google.com/apis/library/sheets.googleapis.com)

## Client

Use the unified client or `SheetsClient` directly.

```python
from googlekit import GoogleKit
from googlekit.gsheets import SheetsClient

# Unified
client = GoogleKit.from_oauth("client_secret.json", services=["gsheets"])
sheets = client.sheets

# Standalone
sheets = SheetsClient.from_oauth("client_secret.json")
# sheets = SheetsClient.from_service_account("sa.json")
# sheets = SheetsClient.from_adc()
```

Factory methods accept `profile=ScopeProfile.READWRITE` (default), optional `scopes=`, and `config=ClientConfig(...)`.

### Managers

| Manager | Role |
| ------- | ---- |
| `sheets.spreadsheets` | Create, get metadata, rename, raw `batchUpdate` |
| `sheets.values` | Read / write / append / clear cell values |
| `sheets.worksheets` | Tabs: create, rename, delete, resize, freeze, hide |
| `sheets.formatting` | Text, numbers, colors, borders, merges, sizes |

---

## A1 ranges

Ranges are ordinary A1 strings. Quote sheet titles that contain spaces or special characters:

| Range | Meaning |
| ----- | ------- |
| `Sheet1!A1` | Single cell |
| `Sheet1!A1:C10` | Block |
| `Sheet1!A:C` | Whole columns (useful for append) |
| `Sheet1!1:1` | Whole row |
| `'Q1 Budget'!A1:B2` | Sheet title with spaces |
| `A1:B2` | Active/first sheet context (prefer explicit sheet names) |

Formatting APIs use **0-based grid indexes** with **exclusive ends** (not A1). Row `0` is the first row; `end_row=1` means “through row 0 only”.

---

## ValueInputOption and render options

```python
from googlekit.gsheets import (
    MajorDimension,
    ValueInputOption,
    ValueRenderOption,
)
```

| Enum | Values | When writing / reading |
| ---- | ------ | ---------------------- |
| `ValueInputOption` | `USER_ENTERED` (default), `RAW` | `USER_ENTERED` parses formulas (`=SUM(A1:A2)`), dates, and numbers like the UI. `RAW` stores strings literally. |
| `ValueRenderOption` | `FORMATTED_VALUE` (default), `UNFORMATTED_VALUE`, `FORMULA` | How cells come back from `read` / `read_multiple`. |
| `MajorDimension` | `ROWS` (default), `COLUMNS` | Orientation of the `values` matrix. |

Date/time render for reads defaults to `"FORMATTED_STRING"` (Sheets `dateTimeRenderOption`). Pass `"SERIAL_NUMBER"` when you need serials.

---

## Models

```python
from googlekit.gsheets import (
    BatchUpdateResponse,
    Spreadsheet,
    UpdateValuesResponse,
    ValueRange,
    Worksheet,
)
```

| Type | Key fields |
| ---- | ---------- |
| `Spreadsheet` | `id`, `title`, `worksheets`, `locale`, `time_zone`, `raw` — helpers `worksheet_by_title`, `worksheet_by_id` |
| `Worksheet` | `sheet_id`, `title`, `index`, `row_count`, `column_count`, freeze counts, `hidden`, `raw` |
| `ValueRange` | `range`, `values`, `major_dimension`, `raw` — `to_api()` for batch writes |
| `UpdateValuesResponse` | `spreadsheet_id`, `updated_range`, `updated_rows`, `updated_columns`, `updated_cells` |
| `BatchUpdateResponse` | `spreadsheet_id`, `replies`, `raw` |

Colors are RGB dicts with floats **0–1** (optional `alpha`): `{"red": 0.85, "green": 0.92, "blue": 1.0}`.

---

## `spreadsheets` — SpreadsheetsManager

### `create`

```python
ss = sheets.spreadsheets.create(
    "Budget 2026",
    locale="en_US",
    time_zone="America/New_York",
    sheet_count=2,  # Sheet1, Sheet2; must be >= 1
)
print(ss.id, ss.title, [w.title for w in ss.worksheets])
```

### `get`

```python
ss = sheets.spreadsheets.get(ss.id)
# Optional: limit metadata / include expensive grid data
ss = sheets.spreadsheets.get(
    ss.id,
    ranges=["Sheet1!A1:Z10"],
    include_grid_data=False,
)
```

### `set_title`

```python
ss = sheets.spreadsheets.set_title(ss.id, "Budget 2026 (final)")
```

Renames via `batchUpdate`, then returns fresh metadata from `get`.

### `batch_update`

Low-level escape hatch for any Sheets `batchUpdate` request objects:

```python
resp = sheets.spreadsheets.batch_update(
    ss.id,
    [
        {
            "updateSpreadsheetProperties": {
                "properties": {"title": "Ops"},
                "fields": "title",
            }
        }
    ],
    include_spreadsheet_in_response=False,
)
print(resp.spreadsheet_id, len(resp.replies))
```

`requests` must be a non-empty list. Prefer high-level managers when they cover the operation.

---

## `values` — ValuesManager

All value methods take `spreadsheet_id` plus an A1 `range_name` (or list of ranges). Matrices are `list[list[cell]]` where a cell is `str | int | float | bool | None`.

### `read`

```python
vr = sheets.values.read(
    ss.id,
    "Sheet1!A1:C10",
    major_dimension=MajorDimension.ROWS,
    value_render_option=ValueRenderOption.FORMATTED_VALUE,
    date_time_render_option="FORMATTED_STRING",
)
print(vr.range, vr.values)
```

Trailing empty cells may be omitted by the API; empty ranges yield `values == []`.

### `read_multiple`

```python
ranges = sheets.values.read_multiple(
    ss.id,
    ["Sheet1!A1:B2", "Sheet1!D1:E2"],
)
for vr in ranges:
    print(vr.range, vr.values)
```

`ranges` must be non-empty.

### `write` / `update`

`write` overwrites a range (`values.update`). `update` is an alias for `write`.

```python
resp = sheets.values.write(
    ss.id,
    "Sheet1!A1:C2",
    [
        ["Name", "Role", "Score"],
        ["Ada", "Engineer", 98],
    ],
    value_input_option=ValueInputOption.USER_ENTERED,
)
print(resp.updated_range, resp.updated_cells)

# Alias
sheets.values.update(ss.id, "Sheet1!A1", [["x"]])
```

### `write_multiple`

Batch several ranges in one request. Pass `ValueRange` instances or dicts with `range` and `values`:

```python
from googlekit.gsheets import ValueRange

raw = sheets.values.write_multiple(
    ss.id,
    [
        ValueRange(range="Sheet1!A1", values=[["Header"]]),
        {"range": "Sheet1!B1", "values": [["Value"]], "majorDimension": "ROWS"},
    ],
    value_input_option=ValueInputOption.USER_ENTERED,
)
print(raw.get("totalUpdatedCells"))
```

Returns the **raw** API dict (includes `totalUpdatedCells`, etc.).

### `append`

Appends after the last row of data in the table detected for the range. Default `insert_data_option="INSERT_ROWS"`.

```python
resp = sheets.values.append(
    ss.id,
    "Sheet1!A:C",
    [
        ["Grace", "Admiral", 100],
        ["Alan", "Mathematician", 99],
    ],
    value_input_option=ValueInputOption.USER_ENTERED,
    insert_data_option="INSERT_ROWS",  # or "OVERWRITE"
)
print(resp.updated_range, resp.updated_rows)
```

### `clear` / `clear_multiple`

Clears **values** only; cell formatting remains.

```python
sheets.values.clear(ss.id, "Sheet1!A2:Z")
sheets.values.clear_multiple(ss.id, ["Sheet1!A2:C100", "Sheet2!A1:B10"])
```

---

## `worksheets` — WorksheetsManager

Most mutations need a numeric `sheet_id` (from `Worksheet.sheet_id`). Use `resolve_sheet_id` when you only know the title.

### `list` / `get_spreadsheet`

```python
tabs = sheets.worksheets.list(ss.id)
for ws in tabs:
    print(ws.sheet_id, ws.title, ws.index)

ss = sheets.worksheets.get_spreadsheet(ss.id)
```

### `create`

```python
ws = sheets.worksheets.create(
    ss.id,
    "Q1",
    rows=2000,
    columns=40,
    index=1,  # optional zero-based tab position
)
print(ws.sheet_id, ws.title)
```

### `rename` / `delete`

```python
sheets.worksheets.rename(ss.id, ws.sheet_id, "Q1-final")
sheets.worksheets.delete(ss.id, ws.sheet_id)
```

### `duplicate`

```python
copy = sheets.worksheets.duplicate(
    ss.id,
    ws.sheet_id,
    new_title="Q1 copy",
    insert_index=0,
)
```

### `reorder`

Move a tab to a new zero-based index:

```python
sheets.worksheets.reorder(ss.id, ws.sheet_id, index=0)
```

### `resize`

Provide `rows` and/or `columns` (each must be a positive int when set):

```python
sheets.worksheets.resize(ss.id, ws.sheet_id, rows=5000, columns=52)
```

### `freeze`

Freeze the first *n* rows and/or columns (`0` clears that freeze):

```python
sheets.worksheets.freeze(ss.id, ws.sheet_id, rows=1, columns=0)
```

### `hide` / `unhide`

```python
sheets.worksheets.hide(ss.id, ws.sheet_id)
sheets.worksheets.unhide(ss.id, ws.sheet_id)
```

### `resolve_sheet_id`

```python
sid = sheets.worksheets.resolve_sheet_id(ss.id, title="Sheet1")
# or pass through an existing id:
sid = sheets.worksheets.resolve_sheet_id(ss.id, sheet_id=0)
```

Raises `NotFoundError` if the title is missing; `ValidationError` if neither `sheet_id` nor `title` is provided.

---

## `formatting` — FormattingManager

All grid ranges are **0-indexed, end exclusive**: `(start_row, end_row, start_col, end_col)`.

Resolve `sheet_id` first, then format.

### `text`

```python
sheets.formatting.text(
    ss.id,
    sheet_id,
    0, 1, 0, 3,  # header row, columns A–C
    bold=True,
    italic=False,
    underline=False,
    strikethrough=False,
    font_size=12,
    font_family="Arial",
    foreground_color={"red": 0.1, "green": 0.1, "blue": 0.1},
)
```

At least one text option is required.

### `number` and `number_format_type`

```python
# Currency
sheets.formatting.number(
    ss.id, sheet_id, 1, 100, 2, 3,
    '"$"#,##0.00',
    number_format_type="CURRENCY",
)

# Percent
sheets.formatting.number(
    ss.id, sheet_id, 1, 100, 3, 4,
    "0.00%",
    number_format_type="PERCENT",
)

# Date
sheets.formatting.number(
    ss.id, sheet_id, 1, 100, 0, 1,
    "yyyy-mm-dd",
    number_format_type="DATE",
)
```

`number_format_type` must be a Sheets `NumberFormat.type`: `NUMBER`, `DATE`, `DATE_TIME`, `TIME`, `PERCENT`, `CURRENCY`, etc. Pattern alone is not enough for correct typing.

### `background`

```python
sheets.formatting.background(
    ss.id, sheet_id, 0, 1, 0, 3,
    {"red": 0.85, "green": 0.92, "blue": 1.0},
)
```

### `alignment`

```python
sheets.formatting.alignment(
    ss.id, sheet_id, 0, 50, 0, 3,
    horizontal="CENTER",   # LEFT | CENTER | RIGHT
    vertical="MIDDLE",     # TOP | MIDDLE | BOTTOM
    wrap_strategy="WRAP",  # OVERFLOW_CELL | CLIP | WRAP
)
```

### `borders` and `colorStyle`

Borders use non-deprecated `Border` fields: `style` plus optional `colorStyle.rgbColor`. The `width` parameter is accepted for compatibility but **ignored** (width is implied by `style`).

```python
sheets.formatting.borders(
    ss.id, sheet_id, 0, 10, 0, 3,
    style="SOLID",  # SOLID, SOLID_MEDIUM, SOLID_THICK, DASHED, DOTTED, ...
    width=1,        # ignored by the API payload
    color={"red": 0.2, "green": 0.2, "blue": 0.2},
    top=True,
    bottom=True,
    left=True,
    right=True,
)
```

Enable at least one side.

### `merge` / `unmerge`

```python
sheets.formatting.merge(
    ss.id, sheet_id, 0, 1, 0, 3,
    merge_type="MERGE_ALL",  # or MERGE_COLUMNS / MERGE_ROWS
)
sheets.formatting.unmerge(ss.id, sheet_id, 0, 1, 0, 3)
```

### `column_widths` / `row_heights`

Indexes are 0-based and end-exclusive; size is pixels:

```python
sheets.formatting.column_widths(ss.id, sheet_id, 0, 3, 140)
sheets.formatting.row_heights(ss.id, sheet_id, 0, 1, 32)
```

### `add_conditional_formatting`

Boolean rule with `CUSTOM_FORMULA`:

```python
sheets.formatting.add_conditional_formatting(
    ss.id, sheet_id, 1, 100, 2, 3,
    formula="=$C2>90",
    background_color={"red": 0.7, "green": 0.95, "blue": 0.7},
    bold=True,
    index=0,
)
```

Provide `background_color` and/or `bold`.

---

## Recipes

### Create, write header, freeze, format

```python
from googlekit.gsheets import SheetsClient, ValueInputOption

sheets = SheetsClient.from_adc()
ss = sheets.spreadsheets.create("Team scores")
sheet_id = ss.worksheets[0].sheet_id

sheets.values.write(
    ss.id,
    "Sheet1!A1:C1",
    [["Name", "Role", "Score"]],
    value_input_option=ValueInputOption.USER_ENTERED,
)
sheets.values.append(
    ss.id,
    "Sheet1!A:C",
    [["Ada", "Engineer", 98], ["Grace", "Admiral", 100]],
)

sheets.worksheets.freeze(ss.id, sheet_id, rows=1)
sheets.formatting.text(ss.id, sheet_id, 0, 1, 0, 3, bold=True, font_size=12)
sheets.formatting.background(
    ss.id, sheet_id, 0, 1, 0, 3,
    {"red": 0.9, "green": 0.9, "blue": 0.95},
)
sheets.formatting.number(
    ss.id, sheet_id, 1, 100, 2, 3, "0", number_format_type="NUMBER"
)
sheets.formatting.borders(ss.id, sheet_id, 0, 3, 0, 3, style="SOLID")
```

### Read formulas vs displayed values

```python
display = sheets.values.read(
    ss.id, "Sheet1!A1:C10",
    value_render_option=ValueRenderOption.FORMATTED_VALUE,
)
formulas = sheets.values.read(
    ss.id, "Sheet1!A1:C10",
    value_render_option=ValueRenderOption.FORMULA,
)
```

### Multi-tab workbook

```python
ss = sheets.spreadsheets.create("Year", sheet_count=1)
q1 = sheets.worksheets.create(ss.id, "Q1")
q2 = sheets.worksheets.duplicate(ss.id, q1.sheet_id, new_title="Q2")
sheets.worksheets.reorder(ss.id, q2.sheet_id, index=0)
sheets.values.write(ss.id, "Q1!A1", [["Q1 data"]])
```

### Raw `batchUpdate` when helpers are not enough

```python
sheets.spreadsheets.batch_update(
    ss.id,
    [{"autoResizeDimensions": {
        "dimensions": {
            "sheetId": sheet_id,
            "dimension": "COLUMNS",
            "startIndex": 0,
            "endIndex": 5,
        }
    }}],
)
```

---

## Pitfalls

- **`USER_ENTERED` vs `RAW`**: formulas and locale-sensitive numbers only parse with `USER_ENTERED`. Use `RAW` when you must store `"=1+1"` as text.
- **A1 vs grid indexes**: values APIs use A1; formatting uses 0-based exclusive ranges. Off-by-one bugs usually mix the two.
- **Sheet titles with spaces**: quote them in A1 (`'My Sheet'!A1`).
- **`append` table detection**: the range (e.g. `Sheet1!A:C`) defines which table is found. Wrong range can append in an unexpected place.
- **`clear` keeps formatting**: to wipe style, send format `batchUpdate` requests or recreate the sheet.
- **`include_grid_data=True`**: expensive; prefer `values.read` for cell data.
- **Borders `width`**: ignored; pick `SOLID` / `SOLID_MEDIUM` / `SOLID_THICK` instead. Colors go through `colorStyle.rgbColor`.
- **`number_format_type`**: mismatching type and pattern (e.g. percent pattern with `NUMBER`) yields wrong display.
- **Empty trailing cells**: API omits them on read; pad in application code if you need a fixed-width matrix.
- **Scopes**: default `READWRITE` / `FULL` use `spreadsheets`. Readonly profiles use `spreadsheets.readonly`. See [scopes](scopes.md).
- **Drive for sharing**: Sheets scopes do not share files; use Drive permissions with Drive API enabled.

---

## Scopes

| Profile | Scope |
| ------- | ----- |
| `metadata` / `readonly` | `https://www.googleapis.com/auth/spreadsheets.readonly` |
| `readwrite` / `full` | `https://www.googleapis.com/auth/spreadsheets` |

```python
from googlekit.auth.scopes import ScopeProfile
from googlekit.gsheets import SheetsClient

sheets = SheetsClient.from_oauth(
    "client_secret.json",
    profile=ScopeProfile.READONLY,
)
```
