"""Typed models for Google Sheets."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ValueInputOption(StrEnum):
    """How input strings are interpreted when writing values."""

    RAW = "RAW"
    USER_ENTERED = "USER_ENTERED"


class ValueRenderOption(StrEnum):
    """How values are rendered when reading."""

    FORMATTED_VALUE = "FORMATTED_VALUE"
    UNFORMATTED_VALUE = "UNFORMATTED_VALUE"
    FORMULA = "FORMULA"


class MajorDimension(StrEnum):
    """Whether values are organized by rows or columns."""

    ROWS = "ROWS"
    COLUMNS = "COLUMNS"


class DateTimeRenderOption(StrEnum):
    """How dates/times/durations are rendered when reading."""

    SERIAL_NUMBER = "SERIAL_NUMBER"
    FORMATTED_STRING = "FORMATTED_STRING"


@dataclass(slots=True)
class GridProperties:
    """Worksheet grid size and freeze settings."""

    row_count: int = 1000
    column_count: int = 26
    frozen_row_count: int = 0
    frozen_column_count: int = 0
    hide_gridlines: bool = False


@dataclass(slots=True)
class Worksheet:
    """A single sheet (tab) within a spreadsheet."""

    sheet_id: int
    title: str
    index: int = 0
    row_count: int = 1000
    column_count: int = 26
    frozen_row_count: int = 0
    frozen_column_count: int = 0
    hidden: bool = False
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Worksheet:
        props = data.get("properties") or {}
        grid = props.get("gridProperties") or {}
        return cls(
            sheet_id=int(props.get("sheetId", 0)),
            title=str(props.get("title", "")),
            index=int(props.get("index", 0)),
            row_count=int(grid.get("rowCount", 1000)),
            column_count=int(grid.get("columnCount", 26)),
            frozen_row_count=int(grid.get("frozenRowCount", 0)),
            frozen_column_count=int(grid.get("frozenColumnCount", 0)),
            hidden=bool(props.get("hidden", False)),
            raw=data,
        )


@dataclass(slots=True)
class Spreadsheet:
    """Spreadsheet metadata and worksheets."""

    id: str
    title: str
    worksheets: list[Worksheet] = field(default_factory=list)
    locale: str | None = None
    time_zone: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Spreadsheet:
        props = data.get("properties") or {}
        sheets = [Worksheet.from_api(s) for s in data.get("sheets") or []]
        return cls(
            id=str(data.get("spreadsheetId", "")),
            title=str(props.get("title", "")),
            worksheets=sheets,
            locale=props.get("locale"),
            time_zone=props.get("timeZone"),
            raw=data,
        )

    def worksheet_by_title(self, title: str) -> Worksheet | None:
        for ws in self.worksheets:
            if ws.title == title:
                return ws
        return None

    def worksheet_by_id(self, sheet_id: int) -> Worksheet | None:
        for ws in self.worksheets:
            if ws.sheet_id == sheet_id:
                return ws
        return None


@dataclass(slots=True)
class ValueRange:
    """Values for a single A1 range."""

    range: str
    values: list[list[Any]] = field(default_factory=list)
    major_dimension: MajorDimension | str = MajorDimension.ROWS
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> ValueRange:
        return cls(
            range=str(data.get("range", "")),
            values=list(data.get("values") or []),
            major_dimension=data.get("majorDimension") or MajorDimension.ROWS,
            raw=data,
        )

    def to_api(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "range": self.range,
            "majorDimension": str(self.major_dimension),
            "values": self.values,
        }
        return body


@dataclass(slots=True)
class UpdateValuesResponse:
    """Result of a values update/write/append call."""

    spreadsheet_id: str
    updated_range: str | None = None
    updated_rows: int = 0
    updated_columns: int = 0
    updated_cells: int = 0
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> UpdateValuesResponse:
        return cls(
            spreadsheet_id=str(data.get("spreadsheetId", "")),
            updated_range=data.get("updatedRange"),
            updated_rows=int(data.get("updatedRows") or 0),
            updated_columns=int(data.get("updatedColumns") or 0),
            updated_cells=int(data.get("updatedCells") or 0),
            raw=data,
        )


@dataclass(slots=True)
class BatchUpdateResponse:
    """Result of spreadsheets.batchUpdate."""

    spreadsheet_id: str
    replies: list[dict[str, Any]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> BatchUpdateResponse:
        return cls(
            spreadsheet_id=str(data.get("spreadsheetId", "")),
            replies=list(data.get("replies") or []),
            raw=data,
        )
