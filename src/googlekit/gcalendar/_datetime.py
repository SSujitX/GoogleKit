"""Timezone-aware datetime helpers for Calendar."""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from googlekit.core.exceptions import ValidationError


def resolve_zone(name: str) -> ZoneInfo:
    """Resolve an IANA timezone name into a :class:`ZoneInfo`."""
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise ValidationError(
            f"Unknown or unavailable timezone: {name!r}. On Windows, install the 'tzdata' package."
        ) from exc
    except Exception as exc:  # pragma: no cover
        raise ValidationError(f"Unknown timezone: {name!r}") from exc


def ensure_aware(
    value: datetime,
    *,
    default_timezone: str | None = None,
    name: str = "datetime",
) -> datetime:
    """Require a timezone-aware datetime, or apply ``default_timezone``.

    Raises:
        ValidationError: When ``value`` is naive and no default timezone is set.
    """
    if not isinstance(value, datetime):
        raise ValidationError(f"{name} must be a datetime instance")
    if value.tzinfo is not None:
        return value
    if default_timezone:
        return value.replace(tzinfo=resolve_zone(default_timezone))
    raise ValidationError(
        f"Naive {name} is not allowed. Pass a timezone-aware datetime "
        "or set ClientConfig.default_timezone."
    )


def to_rfc3339(value: datetime) -> str:
    """Serialize a timezone-aware datetime to RFC3339 / ISO-8601."""
    if value.tzinfo is None:
        raise ValidationError("Cannot serialize naive datetime to RFC3339")
    # Prefer offset form; use Z for UTC.
    if value.utcoffset() == UTC.utcoffset(value):
        return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return value.isoformat()


def date_to_api(value: date) -> str:
    """Serialize a calendar date as ``YYYY-MM-DD``."""
    if isinstance(value, datetime):
        raise ValidationError("Expected date for all-day event, got datetime")
    if not isinstance(value, date):
        raise ValidationError("Expected a date instance")
    return value.isoformat()


def parse_api_datetime(value: str) -> datetime:
    """Parse an RFC3339 datetime string into an aware datetime."""
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def parse_api_date(value: str) -> date:
    """Parse a ``YYYY-MM-DD`` date string."""
    return date.fromisoformat(value)


def event_time_body(
    *,
    start: datetime | date,
    end: datetime | date,
    time_zone: str | None,
    default_timezone: str | None,
    all_day: bool | None = None,
) -> tuple[dict[str, str], dict[str, str]]:
    """Build Calendar API ``start`` / ``end`` objects.

    All-day events use ``date``; timed events use ``dateTime`` (+ optional timeZone).
    """
    inferred_all_day = all_day
    if inferred_all_day is None:
        inferred_all_day = isinstance(start, date) and not isinstance(start, datetime)

    if inferred_all_day:
        start_d = start.date() if isinstance(start, datetime) else start
        end_d = end.date() if isinstance(end, datetime) else end
        return {"date": date_to_api(start_d)}, {"date": date_to_api(end_d)}

    if not isinstance(start, datetime) or not isinstance(end, datetime):
        raise ValidationError("Timed events require datetime start/end")
    start_aware = ensure_aware(start, default_timezone=default_timezone, name="start")
    end_aware = ensure_aware(end, default_timezone=default_timezone, name="end")
    start_body: dict[str, str] = {"dateTime": to_rfc3339(start_aware)}
    end_body: dict[str, str] = {"dateTime": to_rfc3339(end_aware)}
    tz = time_zone or default_timezone
    if tz:
        start_body["timeZone"] = tz
        end_body["timeZone"] = tz
    return start_body, end_body


def combine_local_date(
    day: date,
    hour: int,
    minute: int = 0,
    *,
    tz: str,
) -> datetime:
    """Build an aware datetime from a local date and clock time."""
    return datetime.combine(day, time(hour, minute), tzinfo=resolve_zone(tz))
