"""Regression: shortcuts stay on clients + protocols (IDE autocomplete)."""

from __future__ import annotations

import inspect

import pytest

from googlekit.core.configuration import ClientConfig
from googlekit.core.service_apis import (
    CalendarAPI,
    DocsAPI,
    DriveAPI,
    SheetsAPI,
    SlidesAPI,
)
from googlekit.gcalendar.client import CalendarClient
from googlekit.gdocs.client import DocsClient
from googlekit.gdrive.client import DriveClient
from googlekit.gsheets.client import SheetsClient
from googlekit.gslides.client import SlidesClient

EXPECTED: dict[str, frozenset[str]] = {
    "drive": frozenset(
        {
            "list_files",
            "list_folders",
            "search_files",
            "search_folders",
            "create_folder",
            "upload_file",
            "download_file",
            "upload_folder",
            "delete_file",
            "delete_folder",
            "share",
            "unshare",
            "list_permissions",
            "get_share_link",
        }
    ),
    "sheets": frozenset(
        {
            "create_spreadsheet",
            "get_spreadsheet",
            "read_values",
            "write_values",
            "append_values",
        }
    ),
    "calendar": frozenset(
        {"list_events", "create_event", "get_event", "delete_event"}
    ),
    "docs": frozenset(
        {"create_document", "get_document", "append_text", "insert_text"}
    ),
    "slides": frozenset(
        {"create_presentation", "get_presentation", "add_slide"}
    ),
}

MANAGERS: dict[str, frozenset[str]] = {
    "drive": frozenset({"files", "folders", "permissions", "changes"}),
    "sheets": frozenset({"spreadsheets", "values", "worksheets", "formatting"}),
    "calendar": frozenset({"calendars", "events", "freebusy"}),
    "docs": frozenset({"documents", "content", "tables", "images"}),
    "slides": frozenset(
        {"presentations", "pages", "elements", "text", "images", "tables"}
    ),
}

CASES = [
    ("drive", DriveClient, DriveAPI),
    ("sheets", SheetsClient, SheetsAPI),
    ("calendar", CalendarClient, CalendarAPI),
    ("docs", DocsClient, DocsAPI),
    ("slides", SlidesClient, SlidesAPI),
]


class FakeProvider:
    def credentials(self):
        return object()

    def scopes(self):
        return frozenset()


def _client_shortcuts(client_cls: type, managers: frozenset[str]) -> set[str]:
    skip = {
        "provider",
        "config",
        "transport",
        "from_oauth",
        "from_service_account",
        "from_adc",
        "from_provider",
    }
    names: set[str] = set()
    for cls in client_cls.__mro__:
        if cls is object:
            continue
        for name, val in cls.__dict__.items():
            if name.startswith("_") or name in skip or name in managers:
                continue
            if isinstance(val, (staticmethod, classmethod, property)):
                continue
            if callable(val):
                names.add(name)
    return names


@pytest.mark.parametrize(("key", "client_cls", "proto"), CASES)
def test_shortcuts_on_client_and_protocol(
    key: str, client_cls: type, proto: type
) -> None:
    expected = EXPECTED[key]
    managers = MANAGERS[key]
    found = _client_shortcuts(client_cls, managers)
    assert found == expected, f"{key} client shortcuts mismatch"

    for name in expected:
        assert hasattr(proto, name), f"{proto.__name__} missing {name}"
        assert inspect.getdoc(getattr(client_cls, name)), f"{key}.{name} needs docstring"
        assert inspect.getdoc(getattr(proto, name)), f"{proto.__name__}.{name} needs docstring"

    for name in managers:
        assert hasattr(proto, name), f"{proto.__name__} missing manager {name}"

    inst = client_cls(FakeProvider(), config=ClientConfig())
    assert isinstance(inst, proto)


@pytest.mark.parametrize(("key", "client_cls", "proto"), CASES)
def test_factory_annotated_as_protocol(
    key: str, client_cls: type, proto: type
) -> None:
    hints = inspect.get_annotations(client_cls.from_oauth, eval_str=True)
    assert hints.get("return") is proto, f"{client_cls.__name__}.from_oauth return type"
