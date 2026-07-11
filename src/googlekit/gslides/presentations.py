"""Presentations manager — create, get, batchUpdate, Drive export/share."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from googlekit.core.transport import Transport
from googlekit.core.types import PresentationId
from googlekit.core.validation import require_non_empty
from googlekit.gdocs._drive_bridge import export_via_drive, share_via_drive
from googlekit.gslides.models import BatchUpdateResult, Presentation

SLIDES_MIME = "application/vnd.google-apps.presentation"


class PresentationsManager:
    """Google Slides presentation-level operations (Slides API v1)."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def _service(self) -> Any:
        return self._transport.get_service("slides", "v1")

    def create(self, title: str = "Untitled presentation") -> Presentation:
        """Create a new presentation.

        Args:
            title: Presentation title.

        Returns:
            The created :class:`Presentation`.
        """
        require_non_empty(title, "title")
        request = self._service().presentations().create(body={"title": title})
        data = self._transport.execute(request)
        return Presentation.from_api(data)

    def get(self, presentation_id: PresentationId) -> Presentation:
        """Fetch a presentation including slides and elements.

        Args:
            presentation_id: Presentation ID.

        Returns:
            Typed :class:`Presentation`.
        """
        pid = require_non_empty(presentation_id, "presentation_id")
        request = self._service().presentations().get(presentationId=pid)
        data = self._transport.execute(request)
        return Presentation.from_api(data)

    def batch_update(
        self,
        presentation_id: PresentationId,
        requests: list[dict[str, Any]],
        *,
        write_control: dict[str, Any] | None = None,
    ) -> BatchUpdateResult:
        """Apply one or more Slides ``batchUpdate`` requests atomically.

        Args:
            presentation_id: Presentation ID.
            requests: Slides API request objects.
            write_control: Optional write control.

        Returns:
            :class:`BatchUpdateResult`.
        """
        pid = require_non_empty(presentation_id, "presentation_id")
        body: dict[str, Any] = {"requests": list(requests)}
        if write_control:
            body["writeControl"] = write_control
        request = self._service().presentations().batchUpdate(presentationId=pid, body=body)
        data = self._transport.execute(request)
        return BatchUpdateResult.from_api(data)

    def export(
        self,
        presentation_id: PresentationId,
        export_format: str,
        destination: str | Path | None = None,
    ) -> Any:
        """Export this presentation via the Drive API.

        Requires the ``gdrive`` extra and a Drive OAuth scope. Scopes are
        **not** added automatically.

        Args:
            presentation_id: Presentation ID.
            export_format: Short name (``pdf``, ``pptx``, …) or MIME type.
            destination: Optional local path; omit for in-memory bytes.

        Returns:
            A Drive ``DownloadResult``.

        Raises:
            MissingExtraError: When Google client libraries are missing.
            InsufficientScopesError: When credentials lack Drive scopes.
        """
        pid = require_non_empty(presentation_id, "presentation_id")
        return export_via_drive(
            self._transport.provider,
            pid,
            export_format,
            destination,
            config=self._transport.config,
            source_mime=SLIDES_MIME,
        )

    def share(
        self,
        presentation_id: PresentationId,
        *,
        email: str | None = None,
        role: str = "reader",
        type: str = "user",
        domain: str | None = None,
        send_notification: bool = False,
    ) -> Any:
        """Share this presentation via the Drive Permissions API.

        Requires the ``gdrive`` extra and a Drive write scope. Scopes are
        **not** added automatically.

        Args:
            presentation_id: Presentation ID.
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
        pid = require_non_empty(presentation_id, "presentation_id")
        return share_via_drive(
            self._transport.provider,
            pid,
            email=email,
            role=role,
            type=type,
            domain=domain,
            send_notification=send_notification,
            config=self._transport.config,
        )
