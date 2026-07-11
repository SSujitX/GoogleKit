"""Unit tests for Calendar timezone validation and RFC3339 serialization."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from googlekit.core.configuration import ClientConfig
from googlekit.core.exceptions import ValidationError
from googlekit.core.retries import RetryPolicy
from googlekit.gcalendar._datetime import ensure_aware, event_time_body, to_rfc3339
from googlekit.gcalendar.client import CalendarClient
from googlekit.gcalendar.events import EventsManager
from googlekit.gcalendar.models import SendUpdates

_DHAKA = timezone(timedelta(hours=6))


class _Provider:
    def credentials(self) -> object:
        return object()

    def scopes(self) -> frozenset[str]:
        return frozenset()


def test_ensure_aware_rejects_naive() -> None:
    naive = datetime(2026, 7, 11, 10, 0, 0)
    with pytest.raises(ValidationError, match="Naive"):
        ensure_aware(naive)


def test_ensure_aware_applies_default_timezone() -> None:
    naive = datetime(2026, 7, 11, 10, 0, 0)
    with patch("googlekit.gcalendar._datetime.ZoneInfo", return_value=_DHAKA):
        aware = ensure_aware(naive, default_timezone="Asia/Dhaka")
    assert aware.tzinfo is not None
    assert aware.utcoffset() == timedelta(hours=6)


def test_to_rfc3339_utc_uses_z() -> None:
    dt = datetime(2026, 7, 11, 10, 30, 0, tzinfo=UTC)
    assert to_rfc3339(dt) == "2026-07-11T10:30:00Z"


def test_to_rfc3339_rejects_naive() -> None:
    with pytest.raises(ValidationError):
        to_rfc3339(datetime(2026, 7, 11, 10, 0, 0))


def test_event_time_body_all_day() -> None:
    start, end = event_time_body(
        start=date(2026, 7, 11),
        end=date(2026, 7, 12),
        time_zone=None,
        default_timezone=None,
        all_day=True,
    )
    assert start == {"date": "2026-07-11"}
    assert end == {"date": "2026-07-12"}


def test_event_time_body_all_day_rejects_non_exclusive_end() -> None:
    with pytest.raises(ValidationError, match="exclusive"):
        event_time_body(
            start=date(2026, 7, 11),
            end=date(2026, 7, 11),
            time_zone=None,
            default_timezone=None,
            all_day=True,
        )


def test_event_time_body_timed_requires_aware() -> None:
    with pytest.raises(ValidationError, match="Naive"):
        event_time_body(
            start=datetime(2026, 7, 11, 10, 0, 0),
            end=datetime(2026, 7, 11, 11, 0, 0),
            time_zone=None,
            default_timezone=None,
        )


def test_create_event_payload_and_send_updates() -> None:
    service = MagicMock()
    insert_req = MagicMock()
    insert_req.execute.return_value = {
        "id": "evt1",
        "summary": "Standup",
        "start": {"dateTime": "2026-07-11T10:00:00Z"},
        "end": {"dateTime": "2026-07-11T10:30:00Z"},
    }
    service.events.return_value.insert.return_value = insert_req
    transport = MagicMock()
    transport.config = ClientConfig(
        retry=RetryPolicy(enabled=False, max_attempts=1),
        default_timezone=None,
    )
    transport.get_service.return_value = service
    transport.execute.side_effect = lambda request, **kw: request.execute()
    mgr = EventsManager(transport)
    start = datetime(2026, 7, 11, 10, 0, tzinfo=UTC)
    end = datetime(2026, 7, 11, 10, 30, tzinfo=UTC)
    event = mgr.create(
        "primary",
        summary="Standup",
        start=start,
        end=end,
        attendees=["a@example.com"],
        location="Room A",
        description="Daily sync",
        conference=True,
        send_updates=SendUpdates.NONE,
    )
    assert event.id == "evt1"
    kwargs = service.events.return_value.insert.call_args.kwargs
    assert kwargs["sendUpdates"] == "none"
    assert kwargs["conferenceDataVersion"] == 1
    body = kwargs["body"]
    assert body["summary"] == "Standup"
    assert body["start"]["dateTime"] == "2026-07-11T10:00:00Z"
    assert body["end"]["dateTime"] == "2026-07-11T10:30:00Z"
    assert body["attendees"] == [{"email": "a@example.com"}]
    assert body["location"] == "Room A"
    assert "conferenceData" in body


def test_create_rejects_naive_without_default_tz() -> None:
    transport = MagicMock()
    transport.config = ClientConfig(default_timezone=None)
    transport.get_service.return_value = MagicMock()
    mgr = EventsManager(transport)
    with pytest.raises(ValidationError, match="Naive"):
        mgr.create(
            summary="X",
            start=datetime(2026, 7, 11, 10, 0, 0),
            end=datetime(2026, 7, 11, 11, 0, 0),
        )


def test_create_naive_with_config_default_timezone() -> None:
    service = MagicMock()
    insert_req = MagicMock()
    insert_req.execute.return_value = {
        "id": "evt2",
        "summary": "Local",
        "start": {"dateTime": "2026-07-11T10:00:00+06:00"},
        "end": {"dateTime": "2026-07-11T11:00:00+06:00"},
    }
    service.events.return_value.insert.return_value = insert_req
    transport = MagicMock()
    transport.config = ClientConfig(
        retry=RetryPolicy(enabled=False, max_attempts=1),
        default_timezone="Asia/Dhaka",
    )
    transport.get_service.return_value = service
    transport.execute.side_effect = lambda request, **kw: request.execute()
    mgr = EventsManager(transport)
    with patch("googlekit.gcalendar._datetime.ZoneInfo", return_value=_DHAKA):
        mgr.create(
            summary="Local",
            start=datetime(2026, 7, 11, 10, 0, 0),
            end=datetime(2026, 7, 11, 11, 0, 0),
        )
    body = service.events.return_value.insert.call_args.kwargs["body"]
    assert body["start"]["dateTime"].endswith("+06:00")
    assert body["start"]["timeZone"] == "Asia/Dhaka"


def test_list_with_sync_token_forces_show_deleted() -> None:
    service = MagicMock()
    list_req = MagicMock()
    list_req.execute.return_value = {"items": [], "nextSyncToken": "sync-2"}
    service.events.return_value.list.return_value = list_req
    transport = MagicMock()
    transport.config = ClientConfig(retry=RetryPolicy(enabled=False, max_attempts=1))
    transport.get_service.return_value = service
    transport.execute.side_effect = lambda request, **kw: request.execute()
    mgr = EventsManager(transport)
    mgr.list("primary", sync_token="sync-1", show_deleted=False, q="ignored")
    kwargs = service.events.return_value.list.call_args.kwargs
    assert kwargs["syncToken"] == "sync-1"
    assert kwargs["showDeleted"] is True
    assert "q" not in kwargs
    assert "orderBy" not in kwargs
    assert "timeMin" not in kwargs


def test_calendar_client_managers() -> None:
    client = CalendarClient(_Provider())
    assert client.calendars is not None
    assert client.events is not None
    assert client.freebusy is not None
