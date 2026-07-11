"""Public service API protocols for IDE autocomplete.

Concrete clients (``DriveClient``, …) still expose factories and advanced
attributes (``provider``, ``transport``, …). Annotating unified accessors and
factory return types as these protocols makes ``client.drive.`` suggest
managers (``files``, ``folders``, …) and convenience shortcuts
(``list_files``, ``upload_file``, …) instead of ``from_oauth`` / ``provider``.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, Sequence, runtime_checkable

if TYPE_CHECKING:
    from googlekit.core.pagination import Page
    from googlekit.core.types import (
        A1Range,
        CalendarId,
        DocumentId,
        EventId,
        PresentationId,
        SpreadsheetId,
    )
    from googlekit.gcalendar.calendars import CalendarsManager
    from googlekit.gcalendar.events import EventsManager
    from googlekit.gcalendar.freebusy import FreeBusyManager
    from googlekit.gcalendar.models import Attendee, Event, Reminders, SendUpdates
    from googlekit.gdocs.content import ContentManager
    from googlekit.gdocs.documents import DocumentsManager
    from googlekit.gdocs.images import ImagesManager as DocsImagesManager
    from googlekit.gdocs.models import BatchUpdateResult as DocsBatchUpdateResult
    from googlekit.gdocs.models import Document
    from googlekit.gdocs.tables import TablesManager as DocsTablesManager
    from googlekit.gdrive.changes import ChangesManager
    from googlekit.gdrive.files import FilesManager
    from googlekit.gdrive.folders import FoldersManager
    from googlekit.gdrive.models import (
        DownloadResult,
        DriveFile,
        DriveFolder,
        OverwritePolicy,
        Permission,
        PermissionRole,
        UploadResult,
    )
    from googlekit.gdrive.permissions import PermissionsManager
    from googlekit.gdrive.transfers import ProgressCallback
    from googlekit.gsheets.formatting import FormattingManager
    from googlekit.gsheets.models import (
        MajorDimension,
        Spreadsheet,
        UpdateValuesResponse,
        ValueInputOption,
        ValueRange,
        ValueRenderOption,
    )
    from googlekit.gsheets.spreadsheets import SpreadsheetsManager
    from googlekit.gsheets.values import Matrix, ValuesManager
    from googlekit.gsheets.worksheets import WorksheetsManager
    from googlekit.gslides.elements import ElementsManager
    from googlekit.gslides.images import ImagesManager as SlidesImagesManager
    from googlekit.gslides.models import (
        BatchUpdateResult as SlidesBatchUpdateResult,
    )
    from googlekit.gslides.models import PredefinedLayout, Presentation
    from googlekit.gslides.pages import PagesManager
    from googlekit.gslides.presentations import PresentationsManager
    from googlekit.gslides.tables import TablesManager as SlidesTablesManager
    from googlekit.gslides.text import TextManager


@runtime_checkable
class DriveAPI(Protocol):
    """Drive surface on ``client.drive`` / ``DriveClient.from_*`` results.

    Managers: ``files``, ``folders``, ``permissions``, ``changes``.
    Shortcuts: ``list_files``, ``upload_file``, ``share``, …
    """

    @property
    def files(self) -> FilesManager:
        """File list/search/upload/download/export/metadata/trash."""
        ...

    @property
    def folders(self) -> FoldersManager:
        """Folder create, path helpers, and directory upload/download."""
        ...

    @property
    def permissions(self) -> PermissionsManager:
        """Share with users/groups/domain/anyone and manage permission roles."""
        ...

    @property
    def changes(self) -> ChangesManager:
        """Start-page-token and incremental changes feed."""
        ...

    def list_files(
        self,
        *,
        folder_id: str | None = "root",
        query: str | None = None,
        page_size: int = 100,
        page_token: str | None = None,
        include_trashed: bool = False,
    ) -> Page[DriveFile]:
        """List files (and folders) in a Drive folder — one page.

        Args:
            folder_id: Parent folder id, or ``\"root\"`` for My Drive root.
                Pass ``None`` to search across Drive with ``query`` only.
            query: Extra Drive query language filter.
            page_size: Max items in this page.
            page_token: Continue from a previous page.
            include_trashed: Include trashed items when True.

        Note:
            Default OAuth ``READWRITE`` uses ``drive.file`` and may return an empty
            list. Use ``ScopeProfile.FULL`` or ``READONLY`` to see all of My Drive.
        """
        ...

    def list_folders(
        self,
        *,
        folder_id: str | None = "root",
        page_size: int = 100,
        page_token: str | None = None,
    ) -> Page[DriveFile]:
        """List only folders under ``folder_id`` (default My Drive root)."""
        ...

    def search_files(
        self,
        name_contains: str,
        *,
        page_size: int = 100,
        page_token: str | None = None,
    ) -> Page[DriveFile]:
        """Search files/folders whose name contains ``name_contains``."""
        ...

    def search_folders(
        self,
        name_contains: str,
        *,
        page_size: int = 100,
        page_token: str | None = None,
    ) -> Page[DriveFile]:
        """Search folders whose name contains ``name_contains``."""
        ...

    def create_folder(
        self,
        name: str,
        *,
        parent_id: str | None = None,
    ) -> DriveFolder:
        """Create a folder under ``parent_id`` (or My Drive root)."""
        ...

    def upload_file(
        self,
        path: str | Path,
        *,
        folder_id: str | None = None,
        name: str | None = None,
        overwrite: bool | OverwritePolicy | str = False,
        progress: ProgressCallback | None = None,
    ) -> UploadResult | None:
        """Upload a local file to Drive (``folder_id`` optional destination)."""
        ...

    def download_file(
        self,
        file_id: str,
        destination: str | Path | None = None,
        *,
        export_format: str | None = None,
    ) -> DownloadResult:
        """Download a Drive file (or export a Google-native doc)."""
        ...

    def upload_folder(
        self,
        local_path: str | Path,
        *,
        parent_id: str | None = None,
        overwrite: OverwritePolicy | str = ...,
        progress: ProgressCallback | None = None,
    ) -> DriveFolder:
        """Recursively upload a local directory into Drive."""
        ...

    def delete_file(
        self,
        file_id: str,
        *,
        permanently: bool = False,
    ) -> DriveFile | None:
        """Trash a file, or permanently delete when ``permanently=True``."""
        ...

    def delete_folder(
        self,
        folder_id: str,
        *,
        permanently: bool = False,
    ) -> DriveFile | None:
        """Trash a folder, or permanently delete when ``permanently=True``."""
        ...

    def share(
        self,
        file_id: str,
        *,
        email: str | None = None,
        public: bool = False,
        role: PermissionRole | str = ...,
        notify: bool = True,
    ) -> Permission:
        """Share with a user email, or make link public (requires ``public=True``)."""
        ...

    def unshare(
        self,
        file_id: str,
        *,
        email: str | None = None,
        remove_public: bool = False,
    ) -> int:
        """Remove sharing for an email and/or public (anyone) link."""
        ...

    def list_permissions(self, file_id: str) -> list[Permission]:
        """List who has access to a file or folder."""
        ...

    def get_share_link(
        self,
        file_id: str,
        *,
        role: PermissionRole | str = ...,
        public: bool = True,
    ) -> str:
        """Return a shareable web link (creates anyone permission when ``public=True``)."""
        ...


@runtime_checkable
class SheetsAPI(Protocol):
    """Sheets surface on ``client.sheets``.

    Managers: ``spreadsheets``, ``values``, ``worksheets``, ``formatting``.
    Shortcuts: ``create_spreadsheet``, ``read_values``, ``write_values``, …
    """

    @property
    def spreadsheets(self) -> SpreadsheetsManager:
        """Create/get spreadsheet metadata and raw ``batchUpdate``."""
        ...

    @property
    def values(self) -> ValuesManager:
        """Read / write / append / clear cell values (A1 ranges)."""
        ...

    @property
    def worksheets(self) -> WorksheetsManager:
        """Worksheet tabs: create, rename, delete, resize, freeze, hide."""
        ...

    @property
    def formatting(self) -> FormattingManager:
        """Text, numbers, colors, borders, merges, column/row sizes."""
        ...

    def create_spreadsheet(
        self,
        title: str = "Untitled spreadsheet",
        *,
        locale: str | None = None,
        time_zone: str | None = None,
        sheet_count: int = 1,
    ) -> Spreadsheet:
        """Create a new spreadsheet.

        Args:
            title: Spreadsheet title.
            locale: Optional locale (e.g. ``en_US``).
            time_zone: Optional IANA time zone.
            sheet_count: Number of initial worksheets (minimum 1).
        """
        ...

    def get_spreadsheet(
        self,
        spreadsheet_id: SpreadsheetId,
        *,
        ranges: list[str] | None = None,
        include_grid_data: bool = False,
    ) -> Spreadsheet:
        """Fetch spreadsheet metadata (and optionally grid data).

        Args:
            spreadsheet_id: Spreadsheet ID.
            ranges: Optional A1 ranges to limit returned sheets/data.
            include_grid_data: Include cell grid data when True.
        """
        ...

    def read_values(
        self,
        spreadsheet_id: SpreadsheetId,
        range_name: A1Range,
        *,
        major_dimension: MajorDimension | str = ...,
        value_render_option: ValueRenderOption | str = ...,
        date_time_render_option: str = "FORMATTED_STRING",
    ) -> ValueRange:
        """Read a single A1 range.

        Args:
            spreadsheet_id: Spreadsheet ID.
            range_name: A1 notation (e.g. ``Sheet1!A1:B10``).
        """
        ...

    def write_values(
        self,
        spreadsheet_id: SpreadsheetId,
        range_name: A1Range,
        values: Matrix,
        *,
        value_input_option: ValueInputOption | str = ...,
        major_dimension: MajorDimension | str = ...,
    ) -> UpdateValuesResponse:
        """Overwrite a range with ``values`` (2D list of rows).

        Args:
            spreadsheet_id: Spreadsheet ID.
            range_name: A1 notation to overwrite.
            values: Rows of cell values, e.g. ``[[\"A\", 1], [\"B\", 2]]``.
        """
        ...

    def append_values(
        self,
        spreadsheet_id: SpreadsheetId,
        range_name: A1Range,
        values: Matrix,
        *,
        value_input_option: ValueInputOption | str = ...,
        insert_data_option: str = "INSERT_ROWS",
        major_dimension: MajorDimension | str = ...,
    ) -> UpdateValuesResponse:
        """Append rows after the last row with data in the table.

        Args:
            spreadsheet_id: Spreadsheet ID.
            range_name: A1 range identifying the table (e.g. ``Sheet1!A:B``).
            values: Rows to append.
        """
        ...


@runtime_checkable
class CalendarAPI(Protocol):
    """Calendar surface on ``client.calendar``.

    Managers: ``calendars``, ``events``, ``freebusy``.
    Shortcuts: ``list_events``, ``create_event``, ``get_event``, ``delete_event``.
    """

    @property
    def calendars(self) -> CalendarsManager:
        """Calendar list and secondary calendar CRUD."""
        ...

    @property
    def events(self) -> EventsManager:
        """Event list/CRUD, recurrence, attendees, Meet links."""
        ...

    @property
    def freebusy(self) -> FreeBusyManager:
        """Busy intervals for one or many calendars."""
        ...

    def list_events(
        self,
        calendar_id: CalendarId = "primary",
        *,
        time_min: datetime | None = None,
        time_max: datetime | None = None,
        page_size: int = 100,
        page_token: str | None = None,
        single_events: bool = True,
        order_by: str | None = "startTime",
        q: str | None = None,
        sync_token: str | None = None,
        show_deleted: bool = False,
        time_zone: str | None = None,
    ) -> Page[Event]:
        """List events (one page). Timed bounds must be timezone-aware.

        Args:
            calendar_id: Calendar id (default ``primary``).
            time_min / time_max: Inclusive window (timezone-aware datetimes).
            page_size: Max events in this page.
            q: Free-text search query.
        """
        ...

    def create_event(
        self,
        calendar_id: CalendarId = "primary",
        *,
        summary: str,
        start: datetime | date,
        end: datetime | date,
        description: str | None = None,
        location: str | None = None,
        attendees: Sequence[Attendee | str] | None = None,
        reminders: Reminders | None = None,
        recurrence: Sequence[str] | None = None,
        all_day: bool | None = None,
        time_zone: str | None = None,
        transparency: str | None = None,
        visibility: str | None = None,
        color_id: str | None = None,
        extended_properties: dict[str, Any] | None = None,
        conference: bool = False,
        send_updates: SendUpdates | str = ...,
        status: str | None = None,
    ) -> Event:
        """Create an event on ``calendar_id`` (default primary).

        Timed events require timezone-aware datetimes (or
        ``ClientConfig.default_timezone``). ``send_updates`` defaults to
        ``none`` so invitations are not emailed unless requested.
        """
        ...

    def get_event(self, calendar_id: CalendarId, event_id: EventId) -> Event:
        """Get a single event."""
        ...

    def delete_event(
        self,
        calendar_id: CalendarId,
        event_id: EventId,
        *,
        send_updates: SendUpdates | str = ...,
    ) -> None:
        """Delete an event. ``send_updates`` defaults to ``none``."""
        ...


@runtime_checkable
class DocsAPI(Protocol):
    """Docs surface on ``client.docs``.

    Managers: ``documents``, ``content``, ``tables``, ``images``.
    Shortcuts: ``create_document``, ``get_document``, ``append_text``, ``insert_text``.
    """

    @property
    def documents(self) -> DocumentsManager:
        """Create, get, inspect structure, raw ``batchUpdate``, export, share."""
        ...

    @property
    def content(self) -> ContentManager:
        """Insert/append/replace/delete text, styles, headings, lists, links."""
        ...

    @property
    def tables(self) -> DocsTablesManager:
        """Insert tables, rows/columns, write and format cells."""
        ...

    @property
    def images(self) -> DocsImagesManager:
        """Insert, resize, replace inline images from public URLs."""
        ...

    def create_document(self, title: str = "Untitled document") -> Document:
        """Create a new blank Google Doc."""
        ...

    def get_document(
        self,
        document_id: DocumentId,
        *,
        include_tabs_content: bool = True,
    ) -> Document:
        """Fetch a document including body structure."""
        ...

    def append_text(self, document_id: DocumentId, text: str) -> DocsBatchUpdateResult:
        """Append ``text`` just before the final newline of the body."""
        ...

    def insert_text(
        self,
        document_id: DocumentId,
        text: str,
        index: int,
        *,
        segment_id: str | None = None,
        tab_id: str | None = None,
    ) -> DocsBatchUpdateResult:
        """Insert ``text`` at a UTF-16 ``index`` (body content usually starts at 1)."""
        ...


@runtime_checkable
class SlidesAPI(Protocol):
    """Slides surface on ``client.slides``.

    Managers: ``presentations``, ``pages``, ``elements``, ``text``, ``images``, ``tables``.
    Shortcuts: ``create_presentation``, ``get_presentation``, ``add_slide``.
    """

    @property
    def presentations(self) -> PresentationsManager:
        """Create, get, raw ``batchUpdate``, export, share."""
        ...

    @property
    def pages(self) -> PagesManager:
        """Add / delete / duplicate / reorder slides; list IDs; get page."""
        ...

    @property
    def elements(self) -> ElementsManager:
        """Create shapes, move, resize, transform, group / ungroup."""
        ...

    @property
    def text(self) -> TextManager:
        """Insert / delete / replace / style text and paragraphs."""
        ...

    @property
    def images(self) -> SlidesImagesManager:
        """Insert, replace, position/size images."""
        ...

    @property
    def tables(self) -> SlidesTablesManager:
        """Create tables, write cells, insert/delete rows/cols, format cells."""
        ...

    def create_presentation(self, title: str = "Untitled presentation") -> Presentation:
        """Create a new blank presentation."""
        ...

    def get_presentation(self, presentation_id: PresentationId) -> Presentation:
        """Fetch a presentation including slides."""
        ...

    def add_slide(
        self,
        presentation_id: PresentationId,
        *,
        layout: PredefinedLayout | str = ...,
        insertion_index: int | None = None,
        object_id: str | None = None,
    ) -> SlidesBatchUpdateResult:
        """Add a slide with a predefined layout.

        Args:
            presentation_id: Presentation ID.
            layout: Predefined layout name (default blank).
            insertion_index: Zero-based index; append when omitted.
            object_id: Optional stable object ID for the new slide.
        """
        ...
