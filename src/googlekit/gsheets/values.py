"""Values manager — read, write, append, clear ranges."""

from __future__ import annotations

from typing import Any

from googlekit.core.exceptions import ValidationError
from googlekit.core.transport import Transport
from googlekit.core.types import A1Range, SpreadsheetId
from googlekit.core.validation import require_non_empty
from googlekit.gsheets.models import (
    MajorDimension,
    UpdateValuesResponse,
    ValueInputOption,
    ValueRange,
    ValueRenderOption,
)

CellValue = str | int | float | bool | None
Row = list[CellValue]
Matrix = list[Row]


class ValuesManager:
    """Read and write cell values via the Sheets values API."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def _service(self) -> Any:
        return self._transport.get_service("sheets", "v4")

    def read(
        self,
        spreadsheet_id: SpreadsheetId,
        range_name: A1Range,
        *,
        major_dimension: MajorDimension | str = MajorDimension.ROWS,
        value_render_option: ValueRenderOption | str = ValueRenderOption.FORMATTED_VALUE,
        date_time_render_option: str = "FORMATTED_STRING",
    ) -> ValueRange:
        """Read a single A1 range.

        Empty trailing cells omitted by the API are preserved as returned;
        missing rows are represented as an empty ``values`` list.
        """
        sid = require_non_empty(spreadsheet_id, "spreadsheet_id")
        rng = require_non_empty(range_name, "range_name")
        request = (
            self._service()
            .spreadsheets()
            .values()
            .get(
                spreadsheetId=sid,
                range=rng,
                majorDimension=str(major_dimension),
                valueRenderOption=str(value_render_option),
                dateTimeRenderOption=date_time_render_option,
            )
        )
        data = self._transport.execute(request)
        return ValueRange.from_api(data)

    def read_multiple(
        self,
        spreadsheet_id: SpreadsheetId,
        ranges: list[A1Range],
        *,
        major_dimension: MajorDimension | str = MajorDimension.ROWS,
        value_render_option: ValueRenderOption | str = ValueRenderOption.FORMATTED_VALUE,
        date_time_render_option: str = "FORMATTED_STRING",
    ) -> list[ValueRange]:
        """Read multiple A1 ranges in one request."""
        sid = require_non_empty(spreadsheet_id, "spreadsheet_id")
        if not ranges:
            raise ValidationError("ranges must be a non-empty list")
        for i, r in enumerate(ranges):
            require_non_empty(r, f"ranges[{i}]")
        request = (
            self._service()
            .spreadsheets()
            .values()
            .batchGet(
                spreadsheetId=sid,
                ranges=ranges,
                majorDimension=str(major_dimension),
                valueRenderOption=str(value_render_option),
                dateTimeRenderOption=date_time_render_option,
            )
        )
        data = self._transport.execute(request)
        return [ValueRange.from_api(vr) for vr in data.get("valueRanges") or []]

    def write(
        self,
        spreadsheet_id: SpreadsheetId,
        range_name: A1Range,
        values: Matrix,
        *,
        value_input_option: ValueInputOption | str = ValueInputOption.USER_ENTERED,
        major_dimension: MajorDimension | str = MajorDimension.ROWS,
    ) -> UpdateValuesResponse:
        """Overwrite a range with ``values`` (values.update)."""
        sid = require_non_empty(spreadsheet_id, "spreadsheet_id")
        rng = require_non_empty(range_name, "range_name")
        _validate_matrix(values)
        body = {
            "range": rng,
            "majorDimension": str(major_dimension),
            "values": values,
        }
        request = (
            self._service()
            .spreadsheets()
            .values()
            .update(
                spreadsheetId=sid,
                range=rng,
                valueInputOption=str(value_input_option),
                body=body,
            )
        )
        data = self._transport.execute(request)
        return UpdateValuesResponse.from_api(data)

    def write_multiple(
        self,
        spreadsheet_id: SpreadsheetId,
        data: list[ValueRange] | list[dict[str, Any]],
        *,
        value_input_option: ValueInputOption | str = ValueInputOption.USER_ENTERED,
    ) -> dict[str, Any]:
        """Write multiple ranges in one batchUpdate request.

        Returns:
            Raw API response (includes ``totalUpdatedCells``, etc.).
        """
        sid = require_non_empty(spreadsheet_id, "spreadsheet_id")
        if not data:
            raise ValidationError("data must be a non-empty list")
        value_ranges: list[dict[str, Any]] = []
        for item in data:
            if isinstance(item, ValueRange):
                value_ranges.append(item.to_api())
            else:
                if "range" not in item or "values" not in item:
                    raise ValidationError("each item needs 'range' and 'values'")
                value_ranges.append(
                    {
                        "range": item["range"],
                        "majorDimension": item.get("majorDimension", "ROWS"),
                        "values": item["values"],
                    }
                )
        body = {
            "valueInputOption": str(value_input_option),
            "data": value_ranges,
        }
        request = self._service().spreadsheets().values().batchUpdate(spreadsheetId=sid, body=body)
        result: dict[str, Any] = self._transport.execute(request)
        return result

    def append(
        self,
        spreadsheet_id: SpreadsheetId,
        range_name: A1Range,
        values: Matrix,
        *,
        value_input_option: ValueInputOption | str = ValueInputOption.USER_ENTERED,
        insert_data_option: str = "INSERT_ROWS",
        major_dimension: MajorDimension | str = MajorDimension.ROWS,
    ) -> UpdateValuesResponse:
        """Append rows after the last row with data in the table."""
        sid = require_non_empty(spreadsheet_id, "spreadsheet_id")
        rng = require_non_empty(range_name, "range_name")
        _validate_matrix(values)
        body = {
            "range": rng,
            "majorDimension": str(major_dimension),
            "values": values,
        }
        request = (
            self._service()
            .spreadsheets()
            .values()
            .append(
                spreadsheetId=sid,
                range=rng,
                valueInputOption=str(value_input_option),
                insertDataOption=insert_data_option,
                body=body,
            )
        )
        data = self._transport.execute(request)
        updates = data.get("updates") or data
        return UpdateValuesResponse.from_api(updates)

    def update(
        self,
        spreadsheet_id: SpreadsheetId,
        range_name: A1Range,
        values: Matrix,
        *,
        value_input_option: ValueInputOption | str = ValueInputOption.USER_ENTERED,
        major_dimension: MajorDimension | str = MajorDimension.ROWS,
    ) -> UpdateValuesResponse:
        """Alias for :meth:`write` (values.update)."""
        return self.write(
            spreadsheet_id,
            range_name,
            values,
            value_input_option=value_input_option,
            major_dimension=major_dimension,
        )

    def clear(self, spreadsheet_id: SpreadsheetId, range_name: A1Range) -> dict[str, Any]:
        """Clear values in a single range (formatting is kept)."""
        sid = require_non_empty(spreadsheet_id, "spreadsheet_id")
        rng = require_non_empty(range_name, "range_name")
        request = (
            self._service().spreadsheets().values().clear(spreadsheetId=sid, range=rng, body={})
        )
        result: dict[str, Any] = self._transport.execute(request)
        return result

    def clear_multiple(
        self,
        spreadsheet_id: SpreadsheetId,
        ranges: list[A1Range],
    ) -> dict[str, Any]:
        """Clear multiple ranges in one request."""
        sid = require_non_empty(spreadsheet_id, "spreadsheet_id")
        if not ranges:
            raise ValidationError("ranges must be a non-empty list")
        request = (
            self._service()
            .spreadsheets()
            .values()
            .batchClear(spreadsheetId=sid, body={"ranges": ranges})
        )
        result: dict[str, Any] = self._transport.execute(request)
        return result


def _validate_matrix(values: Matrix) -> None:
    if not isinstance(values, list):
        raise ValidationError("values must be a list of rows")
    for i, row in enumerate(values):
        if not isinstance(row, list):
            raise ValidationError(f"values[{i}] must be a list")
