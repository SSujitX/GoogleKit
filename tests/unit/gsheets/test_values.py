"""Unit tests for Sheets values write payloads."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from googlekit.core.configuration import ClientConfig
from googlekit.core.exceptions import ValidationError
from googlekit.core.retries import RetryPolicy
from googlekit.gsheets.client import SheetsClient
from googlekit.gsheets.models import ValueInputOption, ValueRange
from googlekit.gsheets.values import ValuesManager


class _Provider:
    def credentials(self) -> object:
        return object()

    def scopes(self) -> frozenset[str]:
        return frozenset()


def _values_manager_with_capture() -> tuple[ValuesManager, list[dict[str, Any]], MagicMock]:
    """Return manager, captured kwargs list, and root service mock."""
    captured: list[dict[str, Any]] = []
    service = MagicMock()

    def update(**kwargs: Any) -> MagicMock:
        captured.append(kwargs)
        req = MagicMock()
        req.execute.return_value = {
            "spreadsheetId": kwargs["spreadsheetId"],
            "updatedRange": kwargs["range"],
            "updatedRows": 2,
            "updatedColumns": 2,
            "updatedCells": 4,
        }
        return req

    def append(**kwargs: Any) -> MagicMock:
        captured.append(kwargs)
        req = MagicMock()
        req.execute.return_value = {
            "updates": {
                "spreadsheetId": kwargs["spreadsheetId"],
                "updatedRange": kwargs["range"],
                "updatedRows": 1,
                "updatedColumns": 2,
                "updatedCells": 2,
            }
        }
        return req

    def batch_update(**kwargs: Any) -> MagicMock:
        captured.append(kwargs)
        req = MagicMock()
        req.execute.return_value = {"totalUpdatedCells": 4}
        return req

    values_res = MagicMock()
    values_res.update.side_effect = update
    values_res.append.side_effect = append
    values_res.batchUpdate.side_effect = batch_update
    spreadsheets = MagicMock()
    spreadsheets.values.return_value = values_res
    service.spreadsheets.return_value = spreadsheets

    transport = MagicMock()
    transport.config = ClientConfig(retry=RetryPolicy(enabled=False, max_attempts=1))
    transport.get_service.return_value = service
    transport.execute.side_effect = lambda request, **kw: request.execute()

    return ValuesManager(transport), captured, service


def test_write_payload_user_entered() -> None:
    mgr, captured, _ = _values_manager_with_capture()
    result = mgr.write(
        "sheet123",
        "Sheet1!A1:B2",
        [["Name", "Age"], ["Ada", 36]],
        value_input_option=ValueInputOption.USER_ENTERED,
    )
    assert result.spreadsheet_id == "sheet123"
    assert result.updated_cells == 4
    assert len(captured) == 1
    kwargs = captured[0]
    assert kwargs["spreadsheetId"] == "sheet123"
    assert kwargs["range"] == "Sheet1!A1:B2"
    assert kwargs["valueInputOption"] == "USER_ENTERED"
    assert kwargs["body"] == {
        "range": "Sheet1!A1:B2",
        "majorDimension": "ROWS",
        "values": [["Name", "Age"], ["Ada", 36]],
    }


def test_write_payload_raw_option() -> None:
    mgr, captured, _ = _values_manager_with_capture()
    mgr.write(
        "sheet123",
        "A1",
        [["=1+1"]],
        value_input_option=ValueInputOption.RAW,
    )
    assert captured[0]["valueInputOption"] == "RAW"
    assert captured[0]["body"]["values"] == [["=1+1"]]


def test_write_rejects_non_matrix() -> None:
    mgr, _, _ = _values_manager_with_capture()
    with pytest.raises(ValidationError, match="list of rows"):
        mgr.write("sheet123", "A1", "bad")  # type: ignore[arg-type]


def test_append_payload() -> None:
    mgr, captured, _ = _values_manager_with_capture()
    mgr.append("sheet123", "Sheet1!A:B", [["Bob", 40]])
    kwargs = captured[0]
    assert kwargs["valueInputOption"] == "USER_ENTERED"
    assert kwargs["insertDataOption"] == "INSERT_ROWS"
    assert kwargs["body"]["values"] == [["Bob", 40]]


def test_write_multiple_value_ranges() -> None:
    mgr, captured, _ = _values_manager_with_capture()
    mgr.write_multiple(
        "sheet123",
        [
            ValueRange(range="A1", values=[["x"]]),
            {"range": "B1", "values": [["y"]]},
        ],
    )
    body = captured[0]["body"]
    assert body["valueInputOption"] == "USER_ENTERED"
    assert body["data"][0]["range"] == "A1"
    assert body["data"][1]["range"] == "B1"


def test_sheets_client_managers() -> None:
    client = SheetsClient(_Provider(), config=ClientConfig())
    assert client.spreadsheets is not None
    assert client.values is not None
    assert client.worksheets is not None
    assert client.formatting is not None
