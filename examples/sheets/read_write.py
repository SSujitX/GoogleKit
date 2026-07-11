"""Read and write spreadsheet values with GoogleKit Sheets."""

from __future__ import annotations

from googlekit.gsheets import SheetsClient, ValueInputOption

# Prefer service-account or ADC in automation; OAuth for interactive use.
client = SheetsClient.from_adc()

# Create a spreadsheet, write a header + row, then read it back.
ss = client.spreadsheets.create("GoogleKit read/write demo")
print(f"Created: {ss.id} — {ss.title}")

client.values.write(
    ss.id,
    "Sheet1!A1:C2",
    [
        ["Name", "Role", "Score"],
        ["Ada Lovelace", "Engineer", 98],
    ],
    value_input_option=ValueInputOption.USER_ENTERED,
)

result = client.values.read(ss.id, "Sheet1!A1:C2")
print("Read values:", result.values)
print("Raw response keys:", list(result.raw.keys()))
