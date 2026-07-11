# Google Sheets

Install: `uv add googlekit`

Enable the **Google Sheets API**. Export/share via Drive also needs the Drive API and scopes.

## Client

```python
from googlekit import GoogleKit

kit = GoogleKit.from_oauth("client_secret.json", services=["gsheets"])
sheets = kit.sheets
```

## Managers

| Manager | Role |
| ------- | ---- |
| `sheets.spreadsheets` | Create, metadata, batchUpdate, title |
| `sheets.values` | Read/write/append/clear ranges |
| `sheets.worksheets` | Sheet tabs: create, rename, resize, freeze |
| `sheets.formatting` | Text, numbers, colors, borders, merges |

## Intended values API

```python
sheets.values.read(spreadsheet_id, "Sheet1!A1:D20")
sheets.values.read_many(spreadsheet_id, ["Sheet1!A1:B2", "Sheet1!D1:E2"])
sheets.values.write(spreadsheet_id, "Sheet1!A1", [["a", "b"]])
sheets.values.write_many(spreadsheet_id, {"Sheet1!A1": [["x"]]})
sheets.values.append(spreadsheet_id, "Sheet1!A1", rows)
sheets.values.clear(spreadsheet_id, "Sheet1!A1:Z")
```

Supports `value_input_option`, render options, and `major_dimension`. Empty cells are preserved correctly.
Core operations use ordinary Python sequences/mappings (no pandas required).

## Spreadsheets & worksheets

```python
ss = sheets.spreadsheets.create("Budget")
sheets.spreadsheets.get(ss.id)
sheets.spreadsheets.set_title(ss.id, "Budget 2026")

sheets.worksheets.list(ss.id)
sheets.worksheets.create(ss.id, "Q1")
sheets.worksheets.rename(ss.id, sheet_id, "Q1-final")
sheets.worksheets.delete(ss.id, sheet_id)
sheets.worksheets.resize(ss.id, sheet_id, rows=1000, cols=26)
sheets.worksheets.freeze(ss.id, sheet_id, rows=1, cols=0)
```

## Cross-service notes

- Exporting a spreadsheet uses Drive export helpers
- Sharing uses Drive permissions
- Service accounts need the spreadsheet shared with them unless Workspace delegation is configured
