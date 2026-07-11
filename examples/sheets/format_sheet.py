"""Apply basic formatting to a Google Sheet."""

from __future__ import annotations

from googlekit.gsheets import SheetsClient, ValueInputOption

client = SheetsClient.from_adc()
ss = client.spreadsheets.create("GoogleKit formatting demo")
sheet_id = ss.worksheets[0].sheet_id

client.values.write(
    ss.id,
    "Sheet1!A1:B3",
    [
        ["Metric", "Value"],
        ["Revenue", 1200],
        ["Cost", 450],
    ],
    value_input_option=ValueInputOption.USER_ENTERED,
)

# Header: bold + background
client.formatting.text(ss.id, sheet_id, 0, 1, 0, 2, bold=True, font_size=12)
client.formatting.background(ss.id, sheet_id, 0, 1, 0, 2, {"red": 0.85, "green": 0.92, "blue": 1.0})
client.formatting.column_widths(ss.id, sheet_id, 0, 2, 140)
client.worksheets.freeze(ss.id, sheet_id, rows=1)

print(f"Formatted spreadsheet: {ss.id}")
