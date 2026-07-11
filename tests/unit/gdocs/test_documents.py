"""Unit tests for Google Docs managers (mocked transport)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from googlekit.auth.scopes import Scope, ScopeSet
from googlekit.core.exceptions import InsufficientScopesError, MissingExtraError, ValidationError
from googlekit.core.transport import Transport
from googlekit.gdocs.client import DocsClient
from googlekit.gdocs.content import ContentManager
from googlekit.gdocs.documents import DocumentsManager
from googlekit.gdocs.models import Document, NamedStyleType, TextStyle


class FakeProvider:
    def __init__(self, scopes: frozenset[str] | None = None) -> None:
        self._scopes = scopes or frozenset({str(Scope.DOCUMENTS)})

    def credentials(self) -> Any:
        return object()

    def scopes(self) -> frozenset[str]:
        return self._scopes


@pytest.fixture
def transport() -> Transport:
    return Transport(FakeProvider(), extra="gdocs")


def test_docs_client_managers() -> None:
    client = DocsClient(FakeProvider())
    assert client.documents is not None
    assert client.content is not None
    assert client.tables is not None
    assert client.images is not None
    assert client.provider.scopes() == frozenset({str(Scope.DOCUMENTS)})


def test_document_from_api() -> None:
    raw = {
        "documentId": "doc1",
        "title": "Demo",
        "revisionId": "r1",
        "body": {
            "content": [
                {"startIndex": 0, "endIndex": 1, "sectionBreak": {}},
                {
                    "startIndex": 1,
                    "endIndex": 6,
                    "paragraph": {
                        "elements": [
                            {"textRun": {"content": "Hello"}},
                        ]
                    },
                },
            ]
        },
        "namedRanges": {
            "greeting": {
                "namedRanges": [
                    {
                        "ranges": [{"startIndex": 1, "endIndex": 6}],
                    }
                ]
            }
        },
    }
    doc = Document.from_api(raw)
    assert doc.id == "doc1"
    assert doc.title == "Demo"
    assert doc.body_end_index == 6
    assert doc.plain_text == "Hello"
    assert "greeting" in doc.named_ranges
    assert doc.named_ranges["greeting"][0].start_index == 1


def test_create_and_batch_update(transport: Transport) -> None:
    mgr = DocumentsManager(transport)
    mock_service = MagicMock()
    mock_service.documents().create.return_value = MagicMock()
    mock_service.documents().batchUpdate.return_value = MagicMock()

    with patch.object(transport, "get_service", return_value=mock_service):
        with patch.object(
            transport,
            "execute",
            side_effect=[
                {"documentId": "d1", "title": "T", "body": {"content": []}},
                {"documentId": "d1", "replies": [{}]},
            ],
        ):
            doc = mgr.create("T")
            assert doc.id == "d1"
            result = mgr.batch_update(
                "d1", [{"insertText": {"text": "x", "location": {"index": 1}}}]
            )
            assert result.document_id == "d1"


def test_content_replace_placeholders(transport: Transport) -> None:
    content = ContentManager(transport)
    with patch.object(content._documents, "batch_update") as bu:
        bu.return_value = MagicMock()
        content.replace_placeholders("d1", {"{{name}}": "Ada", "{{role}}": "Engineer"})
        args = bu.call_args[0]
        assert args[0] == "d1"
        assert len(args[1]) == 2


def test_content_insert_validates(transport: Transport) -> None:
    content = ContentManager(transport)
    with pytest.raises(ValidationError):
        content.insert_text("d1", "", 1)
    with pytest.raises(ValidationError):
        content.insert_text("d1", "hi", -1)


def test_set_heading_builds_named_style(transport: Transport) -> None:
    content = ContentManager(transport)
    with patch.object(content._documents, "batch_update") as bu:
        bu.return_value = MagicMock()
        content.set_heading("d1", 1, 10, NamedStyleType.HEADING_1)
        req = bu.call_args[0][1][0]
        assert req["updateParagraphStyle"]["paragraphStyle"]["namedStyleType"] == "HEADING_1"


def test_text_style_to_api() -> None:
    style, fields = TextStyle(bold=True, font_size_pt=14.0, link_url="https://ex.com").to_api()
    assert style["bold"] is True
    assert "fontSize" in style
    assert style["link"]["url"] == "https://ex.com"
    assert "bold" in fields and "link" in fields


def test_export_requires_drive_extra(transport: Transport) -> None:
    mgr = DocumentsManager(transport)
    with patch(
        "googlekit.gdocs._drive_bridge.require_extra",
        side_effect=MissingExtraError("Google Drive", "gdrive"),
    ):
        with pytest.raises(MissingExtraError) as exc:
            mgr.export("d1", "pdf")
        assert "gdrive" in str(exc.value)


def test_export_requires_drive_scopes() -> None:
    provider = FakeProvider(scopes=frozenset({str(Scope.DOCUMENTS)}))
    transport = Transport(provider, extra="gdocs")
    mgr = DocumentsManager(transport)
    with patch("googlekit.gdocs._drive_bridge.require_extra"):
        with pytest.raises(InsufficientScopesError) as exc:
            mgr.export("d1", "pdf")
        assert "Drive" in str(exc.value)


def test_share_requires_drive_write_scopes() -> None:
    provider = FakeProvider(scopes=frozenset({str(Scope.DOCUMENTS), str(Scope.DRIVE_READONLY)}))
    transport = Transport(provider, extra="gdocs")
    mgr = DocumentsManager(transport)
    with patch("googlekit.gdocs._drive_bridge.require_extra"):
        with pytest.raises(InsufficientScopesError):
            mgr.share("d1", email="a@b.com")


def test_share_with_drive_scopes_calls_api() -> None:
    provider = FakeProvider(scopes=frozenset({str(Scope.DOCUMENTS), str(Scope.DRIVE_FILE)}))
    transport = Transport(provider, extra="gdocs")
    mgr = DocumentsManager(transport)
    with patch(
        "googlekit.gdocs.documents.share_via_drive",
        return_value={"id": "perm1"},
    ) as share:
        result = mgr.share("d1", email="a@b.com", role="writer")
        assert result["id"] == "perm1"
        share.assert_called_once()


def test_docs_client_scope_resolution() -> None:
    from googlekit.auth.scopes import ScopeProfile
    from googlekit.gdocs.client import _resolve_scopes

    scopes = ScopeSet.of(Scope.DOCUMENTS)
    assert Scope.DOCUMENTS in _resolve_scopes(None, ScopeProfile.READWRITE).values
    assert _resolve_scopes(scopes, ScopeProfile.READWRITE) is scopes
