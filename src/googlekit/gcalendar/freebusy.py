"""Free/busy query manager."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from googlekit.core.exceptions import ValidationError
from googlekit.core.transport import Transport
from googlekit.core.types import CalendarId
from googlekit.core.validation import require_non_empty
from googlekit.gcalendar._datetime import ensure_aware, to_rfc3339
from googlekit.gcalendar.models import BusyInterval, FreeBusyResponse


class FreeBusyManager:
    """Query free/busy information for one or more calendars."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def _service(self) -> Any:
        return self._transport.get_service("calendar", "v3")

    def query(
        self,
        calendar_ids: CalendarId | list[CalendarId],
        time_min: datetime,
        time_max: datetime,
        *,
        time_zone: str | None = None,
    ) -> FreeBusyResponse:
        """Query busy intervals for one or more calendars.

        Args:
            calendar_ids: A calendar ID or list of IDs.
            time_min: Inclusive start (timezone-aware required unless
                ``ClientConfig.default_timezone`` is set).
            time_max: Exclusive end (same timezone rules).
            time_zone: Optional IANA zone for the query window expansion.

        Returns:
            Typed :class:`FreeBusyResponse` with :class:`BusyInterval` lists.
        """
        ids = _normalize_ids(calendar_ids)
        default_tz = self._transport.config.default_timezone
        aware_min = ensure_aware(time_min, default_timezone=default_tz, name="time_min")
        aware_max = ensure_aware(time_max, default_timezone=default_tz, name="time_max")
        if aware_max <= aware_min:
            raise ValidationError("time_max must be after time_min")
        body: dict[str, Any] = {
            "timeMin": to_rfc3339(aware_min),
            "timeMax": to_rfc3339(aware_max),
            "items": [{"id": cid} for cid in ids],
        }
        tz = time_zone or default_tz
        if tz:
            body["timeZone"] = tz
        request = self._service().freebusy().query(body=body)
        data = self._transport.execute(request)
        calendars: dict[str, list[BusyInterval]] = {}
        for cid, info in (data.get("calendars") or {}).items():
            busy = [BusyInterval.from_api(cid, b) for b in (info.get("busy") or [])]
            calendars[cid] = busy
        return FreeBusyResponse(
            time_min=aware_min,
            time_max=aware_max,
            calendars=calendars,
            raw=data,
        )

    def query_one(
        self,
        calendar_id: CalendarId,
        time_min: datetime,
        time_max: datetime,
        *,
        time_zone: str | None = None,
    ) -> list[BusyInterval]:
        """Query busy intervals for a single calendar."""
        result = self.query(calendar_id, time_min, time_max, time_zone=time_zone)
        return result.calendars.get(calendar_id, [])


def _normalize_ids(calendar_ids: CalendarId | list[CalendarId]) -> list[str]:
    if isinstance(calendar_ids, str):
        return [require_non_empty(calendar_ids, "calendar_id")]
    if not calendar_ids:
        raise ValidationError("calendar_ids must be non-empty")
    return [require_non_empty(c, "calendar_id") for c in calendar_ids]
