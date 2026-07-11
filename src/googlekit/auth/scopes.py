"""OAuth scope constants, presets, and ScopeSet."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import StrEnum


class Scope(StrEnum):
    """Well-known Google OAuth scopes used by GoogleKit."""

    # Drive
    # https://developers.google.com/workspace/drive/api/guides/about-auth
    DRIVE = "https://www.googleapis.com/auth/drive"
    DRIVE_READONLY = "https://www.googleapis.com/auth/drive.readonly"
    DRIVE_FILE = "https://www.googleapis.com/auth/drive.file"
    DRIVE_METADATA = "https://www.googleapis.com/auth/drive.metadata"
    DRIVE_METADATA_READONLY = "https://www.googleapis.com/auth/drive.metadata.readonly"
    DRIVE_APPDATA = "https://www.googleapis.com/auth/drive.appdata"
    DRIVE_APPFOLDER = "https://www.googleapis.com/auth/drive.appfolder"
    DRIVE_APPS_READONLY = "https://www.googleapis.com/auth/drive.apps.readonly"
    DRIVE_MEET_READONLY = "https://www.googleapis.com/auth/drive.meet.readonly"
    DRIVE_INSTALL = "https://www.googleapis.com/auth/drive.install"

    # Sheets
    # https://developers.google.com/workspace/sheets/api/scopes
    SPREADSHEETS = "https://www.googleapis.com/auth/spreadsheets"
    SPREADSHEETS_READONLY = "https://www.googleapis.com/auth/spreadsheets.readonly"

    # Calendar
    # https://developers.google.com/workspace/calendar/api/auth
    CALENDAR = "https://www.googleapis.com/auth/calendar"
    CALENDAR_READONLY = "https://www.googleapis.com/auth/calendar.readonly"
    CALENDAR_EVENTS = "https://www.googleapis.com/auth/calendar.events"
    CALENDAR_EVENTS_READONLY = "https://www.googleapis.com/auth/calendar.events.readonly"
    CALENDAR_EVENTS_FREEBUSY = "https://www.googleapis.com/auth/calendar.events.freebusy"
    CALENDAR_FREEBUSY = "https://www.googleapis.com/auth/calendar.freebusy"
    CALENDAR_CALENDARS = "https://www.googleapis.com/auth/calendar.calendars"
    CALENDAR_CALENDARS_READONLY = "https://www.googleapis.com/auth/calendar.calendars.readonly"
    CALENDAR_CALENDARLIST = "https://www.googleapis.com/auth/calendar.calendarlist"
    CALENDAR_CALENDARLIST_READONLY = (
        "https://www.googleapis.com/auth/calendar.calendarlist.readonly"
    )
    CALENDAR_APP_CREATED = "https://www.googleapis.com/auth/calendar.app.created"
    CALENDAR_SETTINGS_READONLY = "https://www.googleapis.com/auth/calendar.settings.readonly"

    # Docs
    DOCUMENTS = "https://www.googleapis.com/auth/documents"
    DOCUMENTS_READONLY = "https://www.googleapis.com/auth/documents.readonly"

    # Slides
    PRESENTATIONS = "https://www.googleapis.com/auth/presentations"
    PRESENTATIONS_READONLY = "https://www.googleapis.com/auth/presentations.readonly"


_DRIVE_NARROW: frozenset[str] = frozenset(
    {
        Scope.DRIVE_READONLY,
        Scope.DRIVE_FILE,
        Scope.DRIVE_METADATA,
        Scope.DRIVE_METADATA_READONLY,
        Scope.DRIVE_APPDATA,
        Scope.DRIVE_APPFOLDER,
        Scope.DRIVE_APPS_READONLY,
        Scope.DRIVE_MEET_READONLY,
        Scope.DRIVE_INSTALL,
    }
)

_CALENDAR_NARROW: frozenset[str] = frozenset(
    {
        Scope.CALENDAR_READONLY,
        Scope.CALENDAR_EVENTS,
        Scope.CALENDAR_EVENTS_READONLY,
        Scope.CALENDAR_EVENTS_FREEBUSY,
        Scope.CALENDAR_FREEBUSY,
        Scope.CALENDAR_CALENDARS,
        Scope.CALENDAR_CALENDARS_READONLY,
        Scope.CALENDAR_CALENDARLIST,
        Scope.CALENDAR_CALENDARLIST_READONLY,
        Scope.CALENDAR_APP_CREATED,
        Scope.CALENDAR_SETTINGS_READONLY,
    }
)


@dataclass(frozen=True, slots=True)
class ScopeSet:
    """Immutable set of OAuth scope URLs with cover/missing helpers.

    Full ``drive`` / ``calendar`` scopes are treated as covering their narrower
    variants when checking ``covers`` / ``missing``.
    """

    values: frozenset[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", frozenset(self.values))

    @classmethod
    def of(cls, *scopes: str | Scope) -> ScopeSet:
        """Build a set from individual scope strings or :class:`Scope` values."""
        return cls(frozenset(str(s) for s in scopes))

    @classmethod
    def from_iterable(cls, scopes: Iterable[str | Scope]) -> ScopeSet:
        """Build a set from any iterable of scopes."""
        return cls(frozenset(str(s) for s in scopes))

    def union(self, other: ScopeSet | Iterable[str | Scope]) -> ScopeSet:
        """Return a new set containing scopes from both sides."""
        if isinstance(other, ScopeSet):
            return ScopeSet(self.values | other.values)
        return ScopeSet(self.values | frozenset(str(s) for s in other))

    def includes(self, scope: str | Scope) -> bool:
        """True if this exact scope URL is present."""
        return str(scope) in self.values

    def covers(self, required: ScopeSet | Iterable[str | Scope]) -> bool:
        """True if every required scope is granted (with drive/calendar broadening)."""
        return not self.missing(required)

    def missing(self, required: ScopeSet | Iterable[str | Scope]) -> frozenset[str]:
        """Return required scopes not covered by this set."""
        needed = (
            required.values
            if isinstance(required, ScopeSet)
            else frozenset(str(s) for s in required)
        )
        # Full drive / calendar cover narrower scopes (same rules as covers()).
        if Scope.DRIVE in self.values:
            needed = frozenset(s for s in needed if s not in _DRIVE_NARROW)
        if Scope.CALENDAR in self.values:
            needed = frozenset(s for s in needed if s not in _CALENDAR_NARROW)
        return needed - self.values

    def __iter__(self) -> Iterator[str]:
        return iter(self.values)

    def __len__(self) -> int:
        return len(self.values)

    def as_list(self) -> list[str]:
        """Sorted list of scope URLs (stable for logging / auth requests)."""
        return sorted(self.values)


class ScopeProfile(StrEnum):
    """Least-privilege scope presets per service (``metadata`` → ``full``).

    For **Drive**:

    - ``READWRITE`` (default) → ``drive.file`` (only files this app created/opened)
    - ``READONLY`` → ``drive.readonly`` (all files, read)
    - ``FULL`` → ``drive`` (all files, read/write)

    Pass as ``profile=ScopeProfile.FULL`` on ``GoogleKit.auto`` / ``from_oauth``.
    """

    METADATA = "metadata"
    READONLY = "readonly"
    READWRITE = "readwrite"
    FULL = "full"


DRIVE_PRESETS: dict[ScopeProfile, ScopeSet] = {
    ScopeProfile.METADATA: ScopeSet.of(Scope.DRIVE_METADATA_READONLY),
    ScopeProfile.READONLY: ScopeSet.of(Scope.DRIVE_READONLY),
    ScopeProfile.READWRITE: ScopeSet.of(Scope.DRIVE_FILE),
    ScopeProfile.FULL: ScopeSet.of(Scope.DRIVE),
}

SHEETS_PRESETS: dict[ScopeProfile, ScopeSet] = {
    ScopeProfile.METADATA: ScopeSet.of(Scope.SPREADSHEETS_READONLY),
    ScopeProfile.READONLY: ScopeSet.of(Scope.SPREADSHEETS_READONLY),
    ScopeProfile.READWRITE: ScopeSet.of(Scope.SPREADSHEETS),
    ScopeProfile.FULL: ScopeSet.of(Scope.SPREADSHEETS),
}

# CalendarClient exposes events + calendars + freebusy; presets must authorize all three.
CALENDAR_PRESETS: dict[ScopeProfile, ScopeSet] = {
    ScopeProfile.METADATA: ScopeSet.of(Scope.CALENDAR_READONLY),
    ScopeProfile.READONLY: ScopeSet.of(
        Scope.CALENDAR_EVENTS_READONLY,
        Scope.CALENDAR_CALENDARLIST_READONLY,
        Scope.CALENDAR_CALENDARS_READONLY,
        Scope.CALENDAR_FREEBUSY,
    ),
    ScopeProfile.READWRITE: ScopeSet.of(
        Scope.CALENDAR_EVENTS,
        Scope.CALENDAR_CALENDARS,
        Scope.CALENDAR_CALENDARLIST,
        Scope.CALENDAR_FREEBUSY,
    ),
    ScopeProfile.FULL: ScopeSet.of(Scope.CALENDAR),
}

DOCS_PRESETS: dict[ScopeProfile, ScopeSet] = {
    ScopeProfile.METADATA: ScopeSet.of(Scope.DOCUMENTS_READONLY),
    ScopeProfile.READONLY: ScopeSet.of(Scope.DOCUMENTS_READONLY),
    ScopeProfile.READWRITE: ScopeSet.of(Scope.DOCUMENTS),
    ScopeProfile.FULL: ScopeSet.of(Scope.DOCUMENTS),
}

SLIDES_PRESETS: dict[ScopeProfile, ScopeSet] = {
    ScopeProfile.METADATA: ScopeSet.of(Scope.PRESENTATIONS_READONLY),
    ScopeProfile.READONLY: ScopeSet.of(Scope.PRESENTATIONS_READONLY),
    ScopeProfile.READWRITE: ScopeSet.of(Scope.PRESENTATIONS),
    ScopeProfile.FULL: ScopeSet.of(Scope.PRESENTATIONS),
}


def preset_for(service: str, profile: ScopeProfile = ScopeProfile.READWRITE) -> ScopeSet:
    """Return the least-privilege scope preset for a service key.

    ``service`` may be ``gdrive`` / ``drive``, ``gsheets`` / ``sheets``,
    ``gcalendar`` / ``calendar``, ``gdocs`` / ``docs``, ``gslides`` / ``slides``.
    """
    table = {
        "gdrive": DRIVE_PRESETS,
        "drive": DRIVE_PRESETS,
        "gsheets": SHEETS_PRESETS,
        "sheets": SHEETS_PRESETS,
        "gcalendar": CALENDAR_PRESETS,
        "calendar": CALENDAR_PRESETS,
        "gdocs": DOCS_PRESETS,
        "docs": DOCS_PRESETS,
        "gslides": SLIDES_PRESETS,
        "slides": SLIDES_PRESETS,
    }
    presets = table.get(service)
    if presets is None:
        raise ValueError(f"Unknown service for scopes: {service!r}")
    return presets[profile]


def aggregate_scopes(*sets: ScopeSet) -> ScopeSet:
    """Union multiple ScopeSets for the unified client."""
    result: frozenset[str] = frozenset()
    for s in sets:
        result |= s.values
    return ScopeSet(result)
