"""Unit tests for Sheets formatting request construction."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from googlekit.core.configuration import ClientConfig
from googlekit.core.exceptions import ValidationError
from googlekit.core.retries import RetryPolicy
from googlekit.gsheets.formatting import FormattingManager


def test_text_bold_request() -> None:
    service = MagicMock()
    batch_req = MagicMock()
    batch_req.execute.return_value = {"spreadsheetId": "s", "replies": [{}]}
    service.spreadsheets.return_value.batchUpdate.return_value = batch_req
    transport = MagicMock()
    transport.config = ClientConfig(retry=RetryPolicy(enabled=False, max_attempts=1))
    transport.get_service.return_value = service
    transport.execute.side_effect = lambda request, **kw: request.execute()
    mgr = FormattingManager(transport)
    mgr.text("s", 0, 0, 1, 0, 2, bold=True, font_size=12)
    body = service.spreadsheets.return_value.batchUpdate.call_args.kwargs["body"]
    repeat = body["requests"][0]["repeatCell"]
    assert repeat["range"]["sheetId"] == 0
    assert repeat["cell"]["userEnteredFormat"]["textFormat"]["bold"] is True
    assert "fontSize" in repeat["cell"]["userEnteredFormat"]["textFormat"]


def test_merge_and_column_widths() -> None:
    service = MagicMock()
    batch_req = MagicMock()
    batch_req.execute.return_value = {"spreadsheetId": "s", "replies": [{}]}
    service.spreadsheets.return_value.batchUpdate.return_value = batch_req
    transport = MagicMock()
    transport.config = ClientConfig(retry=RetryPolicy(enabled=False, max_attempts=1))
    transport.get_service.return_value = service
    transport.execute.side_effect = lambda request, **kw: request.execute()
    mgr = FormattingManager(transport)
    mgr.merge("s", 0, 0, 2, 0, 3)
    merge_req = service.spreadsheets.return_value.batchUpdate.call_args.kwargs["body"]
    assert "mergeCells" in merge_req["requests"][0]
    mgr.column_widths("s", 0, 0, 3, 120)
    width_req = service.spreadsheets.return_value.batchUpdate.call_args.kwargs["body"]
    dim = width_req["requests"][0]["updateDimensionProperties"]
    assert dim["properties"]["pixelSize"] == 120
    assert dim["range"]["dimension"] == "COLUMNS"


def test_number_format_type() -> None:
    service = MagicMock()
    batch_req = MagicMock()
    batch_req.execute.return_value = {"spreadsheetId": "s", "replies": [{}]}
    service.spreadsheets.return_value.batchUpdate.return_value = batch_req
    transport = MagicMock()
    transport.config = ClientConfig(retry=RetryPolicy(enabled=False, max_attempts=1))
    transport.get_service.return_value = service
    transport.execute.side_effect = lambda request, **kw: request.execute()
    mgr = FormattingManager(transport)
    mgr.number("s", 0, 0, 1, 0, 1, "yyyy-mm-dd", number_format_type="DATE")
    body = service.spreadsheets.return_value.batchUpdate.call_args.kwargs["body"]
    nf = body["requests"][0]["repeatCell"]["cell"]["userEnteredFormat"]["numberFormat"]
    assert nf == {"type": "DATE", "pattern": "yyyy-mm-dd"}


def test_borders_use_color_style() -> None:
    service = MagicMock()
    batch_req = MagicMock()
    batch_req.execute.return_value = {"spreadsheetId": "s", "replies": [{}]}
    service.spreadsheets.return_value.batchUpdate.return_value = batch_req
    transport = MagicMock()
    transport.config = ClientConfig(retry=RetryPolicy(enabled=False, max_attempts=1))
    transport.get_service.return_value = service
    transport.execute.side_effect = lambda request, **kw: request.execute()
    mgr = FormattingManager(transport)
    mgr.borders("s", 0, 0, 1, 0, 1, color={"red": 1.0})
    border = service.spreadsheets.return_value.batchUpdate.call_args.kwargs["body"]["requests"][0][
        "updateBorders"
    ]["top"]
    assert border["style"] == "SOLID"
    assert border["colorStyle"] == {"rgbColor": {"red": 1.0}}
    assert "width" not in border
    assert "color" not in border


def test_invalid_grid_range() -> None:
    transport = MagicMock()
    transport.config = ClientConfig()
    mgr = FormattingManager(transport)
    with pytest.raises(ValidationError, match="Invalid grid range"):
        mgr.background("s", 0, 5, 1, 0, 1, {"red": 1.0})
