"""Unit tests for Sheets spreadsheets and worksheets managers."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from googlekit.core.configuration import ClientConfig
from googlekit.core.retries import RetryPolicy
from googlekit.gsheets.models import Spreadsheet
from googlekit.gsheets.spreadsheets import SpreadsheetsManager
from googlekit.gsheets.worksheets import WorksheetsManager


def _transport(service: MagicMock) -> MagicMock:
    transport = MagicMock()
    transport.config = ClientConfig(retry=RetryPolicy(enabled=False, max_attempts=1))
    transport.get_service.return_value = service
    transport.execute.side_effect = lambda request, **kw: request.execute()
    return transport


def test_create_spreadsheet() -> None:
    service = MagicMock()
    req = MagicMock()
    req.execute.return_value = {
        "spreadsheetId": "abc",
        "properties": {"title": "Budget"},
        "sheets": [{"properties": {"sheetId": 0, "title": "Sheet1", "index": 0}}],
    }
    service.spreadsheets.return_value.create.return_value = req
    mgr = SpreadsheetsManager(_transport(service))
    ss = mgr.create("Budget")
    assert isinstance(ss, Spreadsheet)
    assert ss.id == "abc"
    assert ss.title == "Budget"
    assert ss.worksheets[0].title == "Sheet1"
    body = service.spreadsheets.return_value.create.call_args.kwargs["body"]
    assert body["properties"]["title"] == "Budget"


def test_set_title_batch_update() -> None:
    service = MagicMock()
    batch_req = MagicMock()
    batch_req.execute.return_value = {"spreadsheetId": "abc", "replies": [{}]}
    get_req = MagicMock()
    get_req.execute.return_value = {
        "spreadsheetId": "abc",
        "properties": {"title": "New"},
        "sheets": [],
    }
    spreadsheets = service.spreadsheets.return_value
    spreadsheets.batchUpdate.return_value = batch_req
    spreadsheets.get.return_value = get_req
    mgr = SpreadsheetsManager(_transport(service))
    ss = mgr.set_title("abc", "New")
    assert ss.title == "New"
    body = spreadsheets.batchUpdate.call_args.kwargs["body"]
    assert body["requests"][0]["updateSpreadsheetProperties"]["properties"]["title"] == "New"


def test_worksheet_create() -> None:
    service = MagicMock()
    batch_req = MagicMock()
    batch_req.execute.return_value = {
        "spreadsheetId": "abc",
        "replies": [
            {
                "addSheet": {
                    "properties": {
                        "sheetId": 42,
                        "title": "Data",
                        "index": 1,
                        "gridProperties": {"rowCount": 100, "columnCount": 10},
                    }
                }
            }
        ],
    }
    service.spreadsheets.return_value.batchUpdate.return_value = batch_req
    mgr = WorksheetsManager(_transport(service))
    ws = mgr.create("abc", "Data", rows=100, columns=10)
    assert ws.sheet_id == 42
    assert ws.title == "Data"
    reqs: list[dict[str, Any]] = service.spreadsheets.return_value.batchUpdate.call_args.kwargs[
        "body"
    ]["requests"]
    assert reqs[0]["addSheet"]["properties"]["title"] == "Data"


def test_freeze_and_hide() -> None:
    service = MagicMock()
    batch_req = MagicMock()
    batch_req.execute.return_value = {"spreadsheetId": "abc", "replies": [{}]}
    service.spreadsheets.return_value.batchUpdate.return_value = batch_req
    mgr = WorksheetsManager(_transport(service))
    mgr.freeze("abc", 0, rows=1, columns=2)
    freeze_body = service.spreadsheets.return_value.batchUpdate.call_args.kwargs["body"]
    props = freeze_body["requests"][0]["updateSheetProperties"]["properties"]
    assert props["gridProperties"]["frozenRowCount"] == 1
    assert props["gridProperties"]["frozenColumnCount"] == 2
    mgr.hide("abc", 0)
    hide_body = service.spreadsheets.return_value.batchUpdate.call_args.kwargs["body"]
    assert hide_body["requests"][0]["updateSheetProperties"]["properties"]["hidden"] is True
