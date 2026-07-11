"""Google Drive client entry point."""

from __future__ import annotations

from pathlib import Path

from googlekit.auth.adc import ADCCredentialProvider
from googlekit.auth.oauth import OAuthCredentialProvider
from googlekit.auth.scopes import ScopeProfile, ScopeSet, preset_for
from googlekit.auth.service_account import ServiceAccountCredentialProvider
from googlekit.core.configuration import ClientConfig
from googlekit.core.protocols import CredentialProvider
from googlekit.core.service_apis import DriveAPI
from googlekit.core.transport import Transport
from googlekit.gdrive.changes import ChangesManager
from googlekit.gdrive.files import FilesManager
from googlekit.gdrive.folders import FoldersManager
from googlekit.gdrive.permissions import PermissionsManager


class DriveClient:
    """Typed client for Google Drive API v3.

    Managers (what you use after construction):

    - ``files`` — list/search/upload/download/export/trash
    - ``folders`` — create paths, directory sync
    - ``permissions`` — sharing and links
    - ``changes`` — incremental change feed

    Example::

        from googlekit.gdrive import DriveClient
        from googlekit.auth.scopes import ScopeProfile

        drive = DriveClient.from_oauth(
            "client_secrets.json",
            profile=ScopeProfile.FULL,  # list all My Drive files
        )
        page = drive.files.list(folder_id="root")
    """

    def __init__(
        self,
        provider: CredentialProvider,
        *,
        config: ClientConfig | None = None,
    ) -> None:
        self._provider = provider
        self._config = config or ClientConfig()
        self._transport = Transport(provider, self._config, extra="gdrive")
        self._files: FilesManager | None = None
        self._folders: FoldersManager | None = None
        self._permissions: PermissionsManager | None = None
        self._changes: ChangesManager | None = None

    @classmethod
    def from_oauth(
        cls,
        client_secrets: str | Path,
        token_path: str | Path | None = None,
        scopes: ScopeSet | list[str] | None = None,
        *,
        profile: ScopeProfile = ScopeProfile.READWRITE,
        config: ClientConfig | None = None,
    ) -> DriveAPI:
        """Desktop OAuth. Default profile is ``drive.file`` (app-created files only).

        Use ``profile=ScopeProfile.FULL`` or ``READONLY`` to see the user's full Drive.
        Requires an OAuth **Desktop** client JSON (``installed``), not Web.
        """
        scope_set = _resolve_scopes(scopes, profile)
        provider = OAuthCredentialProvider(
            client_secrets,
            scopes=scope_set,
            token_path=token_path,
            extra="gdrive",
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
    ) -> DriveAPI:
        """Service-account key. Share Drive items with the SA email, or set ``subject`` (DWD)."""
        scope_set = _resolve_scopes(scopes, profile)
        provider = ServiceAccountCredentialProvider(
            credentials_file,
            scopes=scope_set,
            subject=subject,
            extra="gdrive",
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
    ) -> DriveAPI:
        """Application Default Credentials (``gcloud auth application-default login``)."""
        scope_set = _resolve_scopes(scopes, profile)
        provider = ADCCredentialProvider(
            scopes=scope_set,
            quota_project_id=quota_project_id,
            extra="gdrive",
        )
        return cls(provider, config=config)

    @classmethod
    def from_provider(
        cls,
        provider: CredentialProvider,
        *,
        config: ClientConfig | None = None,
    ) -> DriveAPI:
        """Wrap an existing credential provider (e.g. from ``share_provider``)."""
        return cls(provider, config=config)

    @property
    def provider(self) -> CredentialProvider:
        """Credential provider backing this client (advanced)."""
        return self._provider

    @property
    def config(self) -> ClientConfig:
        """Runtime config (timeout, retry, Shared Drives, …)."""
        return self._config

    @property
    def transport(self) -> Transport:
        """HTTP/discovery transport (advanced / tests)."""
        return self._transport

    @property
    def files(self) -> FilesManager:
        """File list/search/upload/download/export/metadata/trash."""
        if self._files is None:
            self._files = FilesManager(self._transport)
        return self._files

    @property
    def folders(self) -> FoldersManager:
        """Folder create, path helpers, and directory upload/download."""
        if self._folders is None:
            self._folders = FoldersManager(self._transport, self.files)
        return self._folders

    @property
    def permissions(self) -> PermissionsManager:
        """Share with users/groups/domain/anyone and manage permission roles."""
        if self._permissions is None:
            self._permissions = PermissionsManager(self._transport)
        return self._permissions

    @property
    def changes(self) -> ChangesManager:
        """Start-page-token and incremental changes feed."""
        if self._changes is None:
            self._changes = ChangesManager(self._transport)
        return self._changes


def _resolve_scopes(
    scopes: ScopeSet | list[str] | None,
    profile: ScopeProfile,
) -> ScopeSet:
    if isinstance(scopes, ScopeSet):
        return scopes
    if scopes is not None:
        return ScopeSet.from_iterable(scopes)
    return preset_for("gdrive", profile)
