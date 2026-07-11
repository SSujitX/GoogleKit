"""Public service API protocols for IDE autocomplete.

Concrete clients (``DriveClient``, …) still expose factories and advanced
attributes (``provider``, ``transport``, …). Annotating unified accessors and
factory return types as these protocols makes ``client.drive.`` suggest
managers (``files``, ``folders``, …) instead of ``from_oauth`` / ``provider``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from googlekit.gcalendar.calendars import CalendarsManager
    from googlekit.gcalendar.events import EventsManager
    from googlekit.gcalendar.freebusy import FreeBusyManager
    from googlekit.gdocs.content import ContentManager
    from googlekit.gdocs.documents import DocumentsManager
    from googlekit.gdocs.images import ImagesManager as DocsImagesManager
    from googlekit.gdocs.tables import TablesManager as DocsTablesManager
    from googlekit.gdrive.changes import ChangesManager
    from googlekit.gdrive.files import FilesManager
    from googlekit.gdrive.folders import FoldersManager
    from googlekit.gdrive.permissions import PermissionsManager
    from googlekit.gsheets.formatting import FormattingManager
    from googlekit.gsheets.spreadsheets import SpreadsheetsManager
    from googlekit.gsheets.values import ValuesManager
    from googlekit.gsheets.worksheets import WorksheetsManager
    from googlekit.gslides.elements import ElementsManager
    from googlekit.gslides.images import ImagesManager as SlidesImagesManager
    from googlekit.gslides.pages import PagesManager
    from googlekit.gslides.presentations import PresentationsManager
    from googlekit.gslides.tables import TablesManager as SlidesTablesManager
    from googlekit.gslides.text import TextManager


@runtime_checkable
class DriveAPI(Protocol):
    """Drive managers shown on ``client.drive`` / ``DriveClient.from_*`` results."""

    @property
    def files(self) -> FilesManager: ...

    @property
    def folders(self) -> FoldersManager: ...

    @property
    def permissions(self) -> PermissionsManager: ...

    @property
    def changes(self) -> ChangesManager: ...


@runtime_checkable
class SheetsAPI(Protocol):
    """Sheets managers shown on ``client.sheets``."""

    spreadsheets: SpreadsheetsManager
    values: ValuesManager
    worksheets: WorksheetsManager
    formatting: FormattingManager


@runtime_checkable
class CalendarAPI(Protocol):
    """Calendar managers shown on ``client.calendar``."""

    calendars: CalendarsManager
    events: EventsManager
    freebusy: FreeBusyManager


@runtime_checkable
class DocsAPI(Protocol):
    """Docs managers shown on ``client.docs``."""

    documents: DocumentsManager
    content: ContentManager
    tables: DocsTablesManager
    images: DocsImagesManager


@runtime_checkable
class SlidesAPI(Protocol):
    """Slides managers shown on ``client.slides``."""

    presentations: PresentationsManager
    pages: PagesManager
    elements: ElementsManager
    text: TextManager
    images: SlidesImagesManager
    tables: SlidesTablesManager
