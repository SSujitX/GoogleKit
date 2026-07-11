"""Unit tests for Calendar freebusy and calendars managers."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from googlekit.core.configuration import ClientConfig
from googlekit.core.exceptions import ValidationError
from googlekit.core.retries import RetryPolicy
from googlekit.gcalendar.calendars import CalendarsManager
from googlekit.gcalendar.freebusy import FreeBusyManager
from googlekit.gcalendar.models import BusyInterval


def _transport(service: MagicMock, **config_kw: object) -> MagicMock:
    transport = MagicMock()
    transport.config = ClientConfig(
        retry=RetryPolicy(enabled=False, max_attempts=1),
        **config_kw,  # type: ignore[arg-type]
    )
    transport.get_service.return_value = service
    transport.execute.side_effect = lambda request, **kw: request.execute()
    return transport


def test_freebusy_query_payload() -> None:
    service = MagicMock()
    req = MagicMock()
    req.execute.return_value = {
        "calendars": {
            "primary": {
                "busy": [
                    {
                        "start": "2026-07-11T10:00:00Z",
                        "end": "2026-07-11T11:00:00Z",
                    }
                ]
            },
            "work@example.com": {"busy": []},
        }
    }
    service.freebusy.return_value.query.return_value = req
    mgr = FreeBusyManager(_transport(service))
    tmin = datetime(2026, 7, 11, 0, 0, tzinfo=UTC)
    tmax = datetime(2026, 7, 12, 0, 0, tzinfo=UTC)
    result = mgr.query(["primary", "work@example.com"], tmin, tmax)
    body = service.freebusy.return_value.query.call_args.kwargs["body"]
    assert body["timeMin"] == "2026-07-11T00:00:00Z"
    assert body["timeMax"] == "2026-07-12T00:00:00Z"
    assert body["items"] == [{"id": "primary"}, {"id": "work@example.com"}]
    assert len(result.calendars["primary"]) == 1
    busy = result.calendars["primary"][0]
    assert isinstance(busy, BusyInterval)
    assert busy.calendar_id == "primary"
    assert result.calendars["work@example.com"] == []


def test_freebusy_rejects_naive() -> None:
    mgr = FreeBusyManager(_transport(MagicMock()))
    with pytest.raises(ValidationError, match="Naive"):
        mgr.query(
            "primary",
            datetime(2026, 7, 11),
            datetime(2026, 7, 12),
        )


def test_calendars_create_secondary() -> None:
    service = MagicMock()
    req = MagicMock()
    req.execute.return_value = {
        "id": "cal123",
        "summary": "Team",
        "timeZone": "UTC",
    }
    service.calendars.return_value.insert.return_value = req
    mgr = CalendarsManager(_transport(service, default_timezone="UTC"))
    cal = mgr.create("Team", description="Shared")
    assert cal.id == "cal123"
    body = service.calendars.return_value.insert.call_args.kwargs["body"]
    assert body["summary"] == "Team"
    assert body["timeZone"] == "UTC"


def test_calendars_list() -> None:
    service = MagicMock()
    req = MagicMock()
    req.execute.return_value = {
        "items": [
            {"id": "primary", "summary": "Me", "primary": True},
            {"id": "x", "summary": "Other"},
        ],
        "nextPageToken": None,
    }
    service.calendarList.return_value.list.return_value = req
    mgr = CalendarsManager(_transport(service))
    page = mgr.list()
    assert len(page.items) == 2
    assert page.items[0].primary is True
