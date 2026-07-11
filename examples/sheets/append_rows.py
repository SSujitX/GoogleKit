"""Append rows to an existing Google Sheet."""

from __future__ import annotations

import os

from googlekit.gsheets import SheetsClient, ValueInputOption

SPREADSHEET_ID = os.environ.get("GOOGLEKIT_SHEET_ID", "YOUR_SPREADSHEET_ID")

client = SheetsClient.from_adc()

response = client.values.append(
    SPREADSHEET_ID,
    "Sheet1!A:C",
    [
        ["Grace Hopper", "Admiral", 100],
        ["Alan Turing", "Mathematician", 99],
    ],
    value_input_option=ValueInputOption.USER_ENTERED,
    insert_data_option="INSERT_ROWS",
)

print(f"Appended to {response.updated_range} ({response.updated_cells} cells)")
