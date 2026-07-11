"""Scope aggregation and ScopeSet behavior."""

from __future__ import annotations

import pytest

from googlekit.auth.scopes import (
    CALENDAR_PRESETS,
    DRIVE_PRESETS,
    SHEETS_PRESETS,
    Scope,
    ScopeProfile,
    ScopeSet,
    aggregate_scopes,
    preset_for,
)


def test_scope_set_of_and_includes() -> None:
    s = ScopeSet.of(Scope.DRIVE_FILE, Scope.SPREADSHEETS)
    assert s.includes(Scope.DRIVE_FILE)
    assert not s.includes(Scope.DRIVE)
    assert len(s) == 2
    assert Scope.DRIVE_FILE in list(s)


def test_scope_set_union() -> None:
    a = ScopeSet.of(Scope.DRIVE_FILE)
    b = ScopeSet.of(Scope.SPREADSHEETS)
    combined = a.union(b)
    assert combined.includes(Scope.DRIVE_FILE)
    assert combined.includes(Scope.SPREADSHEETS)
    assert a.union([Scope.DOCUMENTS]).includes(Scope.DOCUMENTS)


def test_full_drive_covers_narrower_drive_scopes() -> None:
    full = ScopeSet.of(Scope.DRIVE)
    needed = ScopeSet.of(Scope.DRIVE_READONLY, Scope.DRIVE_FILE, Scope.DRIVE_METADATA)
    assert full.covers(needed)
    assert full.missing(needed) == frozenset()


def test_missing_scopes() -> None:
    granted = ScopeSet.of(Scope.DRIVE_FILE)
    needed = ScopeSet.of(Scope.DRIVE_FILE, Scope.SPREADSHEETS)
    missing = granted.missing(needed)
    assert Scope.SPREADSHEETS in missing
    assert Scope.DRIVE_FILE not in missing


def test_covers_false_when_incomplete() -> None:
    granted = ScopeSet.of(Scope.DRIVE_FILE)
    assert not granted.covers([Scope.SPREADSHEETS])


def test_as_list_sorted() -> None:
    s = ScopeSet.of(Scope.SPREADSHEETS, Scope.DRIVE_FILE)
    assert s.as_list() == sorted(s.values)


def test_preset_for_drive_profiles() -> None:
    assert preset_for("gdrive", ScopeProfile.METADATA) == DRIVE_PRESETS[ScopeProfile.METADATA]
    assert preset_for("drive", ScopeProfile.READONLY) == DRIVE_PRESETS[ScopeProfile.READONLY]
    assert preset_for("gdrive", ScopeProfile.READWRITE).includes(Scope.DRIVE_FILE)
    assert preset_for("gdrive", ScopeProfile.FULL).includes(Scope.DRIVE)


def test_preset_for_aliases() -> None:
    assert preset_for("sheets", ScopeProfile.READONLY) == SHEETS_PRESETS[ScopeProfile.READONLY]
    assert preset_for("calendar", ScopeProfile.FULL) == CALENDAR_PRESETS[ScopeProfile.FULL]


def test_preset_for_unknown_raises() -> None:
    with pytest.raises(ValueError, match="Unknown service"):
        preset_for("gphotos", ScopeProfile.READWRITE)


def test_aggregate_scopes_union() -> None:
    combined = aggregate_scopes(
        preset_for("gdrive", ScopeProfile.READWRITE),
        preset_for("gsheets", ScopeProfile.READONLY),
        preset_for("gcalendar", ScopeProfile.READWRITE),
    )
    assert combined.includes(Scope.DRIVE_FILE)
    assert combined.includes(Scope.SPREADSHEETS_READONLY)
    assert combined.includes(Scope.CALENDAR_EVENTS)


def test_from_iterable() -> None:
    s = ScopeSet.from_iterable([Scope.DOCUMENTS, "https://www.googleapis.com/auth/presentations"])
    assert s.includes(Scope.DOCUMENTS)
    assert s.includes(Scope.PRESENTATIONS)
