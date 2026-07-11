"""OAuth scope constants, presets, and ScopeSet."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import StrEnum


class Scope(StrEnum):
    """Well-known Google OAuth scopes used by GoogleKit."""

    # Drive
    DRIVE = "https://www.googleapis.com/auth/drive"
    DRIVE_READONLY = "https://www.googleapis.com/auth/drive.readonly"
    DRIVE_FILE = "https://www.googleapis.com/auth/drive.file"
    DRIVE_METADATA = "https://www.googleapis.com/auth/drive.metadata"
    DRIVE_METADATA_READONLY = "https://www.googleapis.com/auth/drive.metadata.readonly"

    # Sheets
    SPREADSHEETS = "https://www.googleapis.com/auth/spreadsheets"
    SPREADSHEETS_READONLY = "https://www.googleapis.com/auth/spreadsheets.readonly"

    # Calendar
    CALENDAR = "https://www.googleapis.com/auth/calendar"
    CALENDAR_READONLY = "https://www.googleapis.com/auth/calendar.readonly"
    CALENDAR_EVENTS = "https://www.googleapis.com/auth/calendar.events"
    CALENDAR_EVENTS_READONLY = "https://www.googleapis.com/auth/calendar.events.readonly"

    # Docs
    DOCUMENTS = "https://www.googleapis.com/auth/documents"
    DOCUMENTS_READONLY = "https://www.googleapis.com/auth/documents.readonly"

    # Slides
    PRESENTATIONS = "https://www.googleapis.com/auth/presentations"
    PRESENTATIONS_READONLY = "https://www.googleapis.com/auth/presentations.readonly"


@dataclass(frozen=True, slots=True)
class ScopeSet:
    """Immutable set of OAuth scopes with helpers."""

    values: frozenset[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", frozenset(self.values))

    @classmethod
    def of(cls, *scopes: str | Scope) -> ScopeSet:
        return cls(frozenset(str(s) for s in scopes))

    @classmethod
    def from_iterable(cls, scopes: Iterable[str | Scope]) -> ScopeSet:
        return cls(frozenset(str(s) for s in scopes))

    def union(self, other: ScopeSet | Iterable[str | Scope]) -> ScopeSet:
        if isinstance(other, ScopeSet):
            return ScopeSet(self.values | other.values)
        return ScopeSet(self.values | frozenset(str(s) for s in other))

    def includes(self, scope: str | Scope) -> bool:
        return str(scope) in self.values

    def covers(self, required: ScopeSet | Iterable[str | Scope]) -> bool:
        needed = (
            required.values
            if isinstance(required, ScopeSet)
            else frozenset(str(s) for s in required)
        )
        # Full drive covers narrower drive scopes for practical checks.
        if Scope.DRIVE in self.values:
            needed = frozenset(
                s
                for s in needed
                if s
                not in {
                    Scope.DRIVE_READONLY,
                    Scope.DRIVE_FILE,
                    Scope.DRIVE_METADATA,
                    Scope.DRIVE_METADATA_READONLY,
                }
            )
        return needed <= self.values

    def missing(self, required: ScopeSet | Iterable[str | Scope]) -> frozenset[str]:
        needed = (
            required.values
            if isinstance(required, ScopeSet)
            else frozenset(str(s) for s in required)
        )
        if self.covers(needed):
            return frozenset()
        return needed - self.values

    def __iter__(self) -> Iterator[str]:
        return iter(self.values)

    def __len__(self) -> int:
        return len(self.values)

    def as_list(self) -> list[str]:
        return sorted(self.values)


class ScopeProfile(StrEnum):
    """Least-privilege scope profiles per service."""

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

CALENDAR_PRESETS: dict[ScopeProfile, ScopeSet] = {
    ScopeProfile.METADATA: ScopeSet.of(Scope.CALENDAR_READONLY),
    ScopeProfile.READONLY: ScopeSet.of(Scope.CALENDAR_EVENTS_READONLY),
    ScopeProfile.READWRITE: ScopeSet.of(Scope.CALENDAR_EVENTS),
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
    """Return the scope preset for a service name."""
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
