"""Unit tests for Google Slides managers (mocked transport)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from googlekit.auth.scopes import Scope, ScopeSet
from googlekit.core.exceptions import InsufficientScopesError, MissingExtraError, ValidationError
from googlekit.core.transport import Transport
from googlekit.gslides.client import SlidesClient
from googlekit.gslides.elements import ElementsManager
from googlekit.gslides.models import (
    AffineTransform,
    PredefinedLayout,
    Presentation,
    Size,
    pt_to_emu,
)
from googlekit.gslides.pages import PagesManager
from googlekit.gslides.presentations import PresentationsManager
from googlekit.gslides.text import TextManager


class FakeProvider:
    def __init__(self, scopes: frozenset[str] | None = None) -> None:
        self._scopes = scopes or frozenset({str(Scope.PRESENTATIONS)})

    def credentials(self) -> Any:
        return object()

    def scopes(self) -> frozenset[str]:
        return self._scopes


@pytest.fixture
def transport() -> Transport:
    return Transport(FakeProvider(), extra="gslides")


def test_slides_client_managers() -> None:
    client = SlidesClient(FakeProvider())
    assert client.presentations is not None
    assert client.pages is not None
    assert client.elements is not None
    assert client.text is not None
    assert client.images is not None
    assert client.tables is not None


def test_presentation_from_api() -> None:
    raw = {
        "presentationId": "p1",
        "title": "Deck",
        "slides": [
            {
                "objectId": "s1",
                "slideProperties": {"layoutObjectId": "l1"},
                "pageElements": [
                    {
                        "objectId": "e1",
                        "size": {
                            "width": {"magnitude": 100, "unit": "EMU"},
                            "height": {"magnitude": 50, "unit": "EMU"},
                        },
                        "shape": {},
                    }
                ],
            }
        ],
        "pageSize": {
            "width": {"magnitude": 9144000, "unit": "EMU"},
            "height": {"magnitude": 5143500, "unit": "EMU"},
        },
    }
    pres = Presentation.from_api(raw)
    assert pres.id == "p1"
    assert pres.slide_ids() == ["s1"]
    assert pres.slides[0].elements[0].kind == "shape"
    assert pres.page_size is not None
    assert pres.page_size.width_emu == 9144000


def test_size_and_transform() -> None:
    sz = Size.from_pt(72, 36)
    assert sz.width_emu == pt_to_emu(72)
    assert sz.height_emu == pt_to_emu(36)
    with pytest.raises(ValidationError):
        Size.from_pt(0, 10)
    tf = AffineTransform.translate_pt(10, 20)
    api = tf.to_api()
    assert api["translateX"] == float(pt_to_emu(10))
    assert api["unit"] == "EMU"


def test_create_presentation(transport: Transport) -> None:
    mgr = PresentationsManager(transport)
    mock_service = MagicMock()
    with patch.object(transport, "get_service", return_value=mock_service):
        with patch.object(
            transport,
            "execute",
            return_value={"presentationId": "p1", "title": "T", "slides": []},
        ):
            pres = mgr.create("T")
            assert pres.id == "p1"


def test_pages_add_and_reorder(transport: Transport) -> None:
    pages = PagesManager(transport)
    with patch.object(pages._presentations, "batch_update") as bu:
        bu.return_value = MagicMock()
        pages.add("p1", layout=PredefinedLayout.TITLE_AND_BODY, insertion_index=1)
        req = bu.call_args[0][1][0]
        assert req["createSlide"]["slideLayoutReference"]["predefinedLayout"] == ("TITLE_AND_BODY")
        pages.reorder("p1", ["s2", "s1"], 0)
        req2 = bu.call_args[0][1][0]
        assert req2["updateSlidesPosition"]["insertionIndex"] == 0


def test_elements_create_shape(transport: Transport) -> None:
    elements = ElementsManager(transport)
    with patch.object(elements._presentations, "batch_update") as bu:
        bu.return_value = MagicMock()
        elements.create_shape("p1", "s1", object_id="box1", width_pt=100, height_pt=50)
        create = bu.call_args[0][1][0]["createShape"]
        assert create["objectId"] == "box1"
        assert create["elementProperties"]["pageObjectId"] == "s1"
        assert "size" in create["elementProperties"]


def test_elements_group_requires_two(transport: Transport) -> None:
    elements = ElementsManager(transport)
    with pytest.raises(ValidationError):
        elements.group("p1", ["only-one"])


def test_text_replace_placeholders(transport: Transport) -> None:
    text = TextManager(transport)
    with patch.object(text._presentations, "batch_update") as bu:
        bu.return_value = MagicMock()
        text.replace_placeholders("p1", {"{{title}}": "Q3", "{{name}}": "Ada"})
        assert len(bu.call_args[0][1]) == 2


def test_export_requires_drive_extra(transport: Transport) -> None:
    mgr = PresentationsManager(transport)
    with patch(
        "googlekit.gdocs._drive_bridge.require_extra",
        side_effect=MissingExtraError("Google Drive", "gdrive"),
    ):
        with pytest.raises(MissingExtraError):
            mgr.export("p1", "pdf")


def test_export_requires_drive_scopes() -> None:
    provider = FakeProvider(scopes=frozenset({str(Scope.PRESENTATIONS)}))
    transport = Transport(provider, extra="gslides")
    mgr = PresentationsManager(transport)
    with patch("googlekit.gdocs._drive_bridge.require_extra"):
        with pytest.raises(InsufficientScopesError):
            mgr.export("p1", "pptx")


def test_slides_scope_resolution() -> None:
    from googlekit.auth.scopes import ScopeProfile
    from googlekit.gslides.client import _resolve_scopes

    assert Scope.PRESENTATIONS in _resolve_scopes(None, ScopeProfile.READWRITE).values
    s = ScopeSet.of(Scope.PRESENTATIONS_READONLY)
    assert _resolve_scopes(s, ScopeProfile.READONLY) is s
