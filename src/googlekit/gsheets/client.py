"""Google Sheets client."""

from __future__ import annotations

from pathlib import Path

from googlekit.auth.adc import ADCCredentialProvider
from googlekit.auth.oauth import OAuthCredentialProvider
from googlekit.auth.scopes import ScopeProfile, ScopeSet, preset_for
from googlekit.auth.service_account import ServiceAccountCredentialProvider
from googlekit.core.configuration import ClientConfig
from googlekit.core.protocols import CredentialProvider
from googlekit.core.service_apis import SheetsAPI
from googlekit.core.transport import Transport
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


class SheetsClient:
    """High-level Google Sheets API client.

    Managers: ``spreadsheets``, ``values``, ``worksheets``, ``formatting``.

    Shortcuts: ``create_spreadsheet``, ``get_spreadsheet``, ``read_values``,
    ``write_values``, ``append_values``.
    """

    def __init__(
        self,
        provider: CredentialProvider,
        *,
        config: ClientConfig | None = None,
    ) -> None:
        self._provider = provider
        self._config = config or ClientConfig()
        self._transport = Transport(provider, self._config, extra="gsheets")
        self.spreadsheets = SpreadsheetsManager(self._transport)
        self.values = ValuesManager(self._transport)
        self.worksheets = WorksheetsManager(self._transport)
        self.formatting = FormattingManager(self._transport)

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
        return self.spreadsheets.create(
            title,
            locale=locale,
            time_zone=time_zone,
            sheet_count=sheet_count,
        )

    def get_spreadsheet(
        self,
        spreadsheet_id: str,
        *,
        ranges: list[str] | None = None,
        include_grid_data: bool = False,
    ) -> Spreadsheet:
        """Fetch spreadsheet metadata (and optionally grid data)."""
        return self.spreadsheets.get(
            spreadsheet_id,
            ranges=ranges,
            include_grid_data=include_grid_data,
        )

    def read_values(
        self,
        spreadsheet_id: str,
        range_name: str,
        *,
        major_dimension: MajorDimension | str = MajorDimension.ROWS,
        value_render_option: ValueRenderOption | str = ValueRenderOption.FORMATTED_VALUE,
        date_time_render_option: str = "FORMATTED_STRING",
    ) -> ValueRange:
        """Read a single A1 range.

        Args:
            spreadsheet_id: Spreadsheet ID.
            range_name: A1 notation (e.g. ``Sheet1!A1:B10``).
        """
        return self.values.read(
            spreadsheet_id,
            range_name,
            major_dimension=major_dimension,
            value_render_option=value_render_option,
            date_time_render_option=date_time_render_option,
        )

    def write_values(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: Matrix,
        *,
        value_input_option: ValueInputOption | str = ValueInputOption.USER_ENTERED,
        major_dimension: MajorDimension | str = MajorDimension.ROWS,
    ) -> UpdateValuesResponse:
        """Overwrite a range with ``values`` (2D list of rows).

        Args:
            spreadsheet_id: Spreadsheet ID.
            range_name: A1 notation to overwrite.
            values: Rows of cell values, e.g. ``[[\"A\", 1], [\"B\", 2]]``.
        """
        return self.values.write(
            spreadsheet_id,
            range_name,
            values,
            value_input_option=value_input_option,
            major_dimension=major_dimension,
        )

    def append_values(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: Matrix,
        *,
        value_input_option: ValueInputOption | str = ValueInputOption.USER_ENTERED,
        insert_data_option: str = "INSERT_ROWS",
        major_dimension: MajorDimension | str = MajorDimension.ROWS,
    ) -> UpdateValuesResponse:
        """Append rows after the last row with data in the table.

        Args:
            spreadsheet_id: Spreadsheet ID.
            range_name: A1 range identifying the table (e.g. ``Sheet1!A:B``).
            values: Rows to append.
        """
        return self.values.append(
            spreadsheet_id,
            range_name,
            values,
            value_input_option=value_input_option,
            insert_data_option=insert_data_option,
            major_dimension=major_dimension,
        )

    @property
    def provider(self) -> CredentialProvider:
        """Credential provider backing this client (advanced)."""
        return self._provider

    @property
    def config(self) -> ClientConfig:
        """Runtime config (timeout, retry, …)."""
        return self._config

    @property
    def transport(self) -> Transport:
        """HTTP/discovery transport (advanced / tests)."""
        return self._transport

    @classmethod
    def from_oauth(
        cls,
        client_secrets: str | Path,
        token_path: str | Path | None = None,
        scopes: ScopeSet | list[str] | None = None,
        *,
        profile: ScopeProfile = ScopeProfile.READWRITE,
        config: ClientConfig | None = None,
    ) -> SheetsAPI:
        """Create a Sheets client using desktop OAuth."""
        scope_set = _resolve_scopes(scopes, profile)
        provider = OAuthCredentialProvider(
            client_secrets,
            scopes=scope_set,
            token_path=token_path,
            extra="gsheets",
        )
        return cls(provider, config=config)

    @classmethod
    def from_service_account(
        cls,
        credentials_file: str | Path,
        subject: str | None = None,
        scopes: ScopeSet | list[str] | None = None,
        *,
        profile: ScopeProfile = ScopeProfile.READWRITE,
        config: ClientConfig | None = None,
    ) -> SheetsAPI:
        """Create a Sheets client using a service-account JSON key."""
        scope_set = _resolve_scopes(scopes, profile)
        provider = ServiceAccountCredentialProvider(
            credentials_file,
            scopes=scope_set,
            subject=subject,
            extra="gsheets",
        )
        return cls(provider, config=config)

    @classmethod
    def from_adc(
        cls,
        quota_project_id: str | None = None,
        scopes: ScopeSet | list[str] | None = None,
        *,
        profile: ScopeProfile = ScopeProfile.READWRITE,
        config: ClientConfig | None = None,
    ) -> SheetsAPI:
        """Create a Sheets client using Application Default Credentials."""
        scope_set = _resolve_scopes(scopes, profile)
        provider = ADCCredentialProvider(
            scopes=scope_set,
            quota_project_id=quota_project_id,
            extra="gsheets",
        )
        return cls(provider, config=config)


def _resolve_scopes(
    scopes: ScopeSet | list[str] | None,
    profile: ScopeProfile,
) -> ScopeSet:
    if isinstance(scopes, ScopeSet):
        return scopes
    if scopes is not None:
        return ScopeSet.from_iterable(scopes)
    return preset_for("gsheets", profile)
