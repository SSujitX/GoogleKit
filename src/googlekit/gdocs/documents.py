"""Documents manager — create, get, inspect, batchUpdate, Drive export/share."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from googlekit.core.transport import Transport
from googlekit.core.types import DocumentId
from googlekit.core.validation import require_non_empty
from googlekit.gdocs._drive_bridge import export_via_drive, share_via_drive
from googlekit.gdocs.models import BatchUpdateResult, Document, StructuralElement

DOCS_MIME = "application/vnd.google-apps.document"


class DocumentsManager:
    """Google Docs document-level operations (Docs API v1)."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def _service(self) -> Any:
        return self._transport.get_service("docs", "v1")

    def create(self, title: str = "Untitled document") -> Document:
        """Create a new blank Google Doc.

        Args:
            title: Document title.

        Returns:
            The created :class:`Document`.
        """
        require_non_empty(title, "title")
        request = self._service().documents().create(body={"title": title})
        data = self._transport.execute(request)
        return Document.from_api(data)

    def get(self, document_id: DocumentId) -> Document:
        """Fetch a document including body structure.

        Args:
            document_id: Document ID.

        Returns:
            Typed :class:`Document`.
        """
        did = require_non_empty(document_id, "document_id")
        request = self._service().documents().get(documentId=did)
        data = self._transport.execute(request)
        return Document.from_api(data)

    def inspect_structure(self, document_id: DocumentId) -> list[StructuralElement]:
        """Return structural elements from the document body.

        Args:
            document_id: Document ID.

        Returns:
            List of :class:`StructuralElement` values (paragraphs, tables, …).
        """
        return list(self.get(document_id).structural_elements)

    def batch_update(
        self,
        document_id: DocumentId,
        requests: list[dict[str, Any]],
        *,
        write_control: dict[str, Any] | None = None,
    ) -> BatchUpdateResult:
        """Apply one or more Docs ``batchUpdate`` requests atomically.

        Indexes in requests must use UTF-16 code units. See
        :mod:`googlekit.gdocs.utf16`.

        Args:
            document_id: Document ID.
            requests: Docs API request objects.
            write_control: Optional ``writeControl`` (e.g. requiredRevisionId).

        Returns:
            :class:`BatchUpdateResult` with per-request replies.
        """
        did = require_non_empty(document_id, "document_id")
        body: dict[str, Any] = {"requests": list(requests)}
        if write_control:
            body["writeControl"] = write_control
        request = self._service().documents().batchUpdate(documentId=did, body=body)
        data = self._transport.execute(request)
        return BatchUpdateResult.from_api(data)

    def export(
        self,
        document_id: DocumentId,
        export_format: str,
        destination: str | Path | None = None,
    ) -> Any:
        """Export this document via the Drive API.

        Requires the ``gdrive`` extra and a Drive OAuth scope
        (``drive``, ``drive.readonly``, or ``drive.file``). Scopes are **not**
        added automatically.

        Args:
            document_id: Document ID.
            export_format: Short name (``pdf``, ``docx``, ``txt``, …) or MIME.
            destination: Optional local path; omit to receive bytes in memory.

        Returns:
            A Drive ``DownloadResult``.

        Raises:
            MissingExtraError: When Google client libraries are missing.
            InsufficientScopesError: When credentials lack Drive scopes.
        """
        did = require_non_empty(document_id, "document_id")
        return export_via_drive(
            self._transport.provider,
            did,
            export_format,
            destination,
            config=self._transport.config,
            source_mime=DOCS_MIME,
        )

    def share(
        self,
        document_id: DocumentId,
        *,
        email: str | None = None,
        role: str = "reader",
        type: str = "user",
        domain: str | None = None,
        send_notification: bool = False,
    ) -> Any:
        """Share this document via the Drive Permissions API.

        Requires the ``gdrive`` extra and a Drive write scope (``drive`` or
        ``drive.file``). Scopes are **not** added automatically.

        Args:
            document_id: Document ID.
            email: Recipient email for user/group shares.
            role: ``reader``, ``commenter``, or ``writer``.
            type: ``user``, ``group``, ``domain``, or ``anyone``.
            domain: Required for domain shares.
            send_notification: Email the recipient when True.

        Returns:
            A Drive ``Permission`` (or raw dict).

        Raises:
            MissingExtraError: When Google client libraries are missing.
            InsufficientScopesError: When credentials lack Drive write scopes.
        """
        did = require_non_empty(document_id, "document_id")
        return share_via_drive(
            self._transport.provider,
            did,
            email=email,
            role=role,
            type=type,
            domain=domain,
            send_notification=send_notification,
            config=self._transport.config,
        )
