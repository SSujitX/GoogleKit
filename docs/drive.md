---
title: Google Drive API Python client (GoogleKit)
description: >-
  Upload, download, search, share, and export Google Drive files with GoogleKit.
  Typed DriveClient for Drive API v3 — folders, permissions, changes, Shared Drives.
---

# Google Drive

Reference for **GoogleKit Drive** (`googlekit.gdrive`) — a typed client for
[Google Drive API v3](https://developers.google.com/workspace/drive/api/reference/rest/v3).

**Official Google docs:** [Drive API guides](https://developers.google.com/workspace/drive/api/guides/about-sdk) ·
[REST reference](https://developers.google.com/workspace/drive/api/reference/rest/v3) ·
[Files](https://developers.google.com/workspace/drive/api/reference/rest/v3/files) ·
[Permissions](https://developers.google.com/workspace/drive/api/reference/rest/v3/permissions) ·
[Changes](https://developers.google.com/workspace/drive/api/reference/rest/v3/changes) ·
[Enable API](https://console.cloud.google.com/apis/library/drive.googleapis.com)

Site: [https://ssujitx.github.io/GoogleKit/](https://ssujitx.github.io/GoogleKit/)

## Overview

Install and enable the API:

```bash
uv add googlekit
```

In [Google Cloud Console](https://console.cloud.google.com/), enable the **Google Drive API** for your project and create OAuth client credentials (desktop) and/or a service-account key as needed.

GoogleKit Drive exposes four managers on a single client:

| Manager | Attribute | Role |
| ------- | --------- | ---- |
| `FilesManager` | `drive.files` | List, search, upload, download, export, metadata, trash, delete |
| `FoldersManager` | `drive.folders` | Create folders/paths, list children, recursive directory sync |
| `PermissionsManager` | `drive.permissions` | Share with users/groups/domain/anyone, roles, shareable links |
| `ChangesManager` | `drive.changes` | Start page token and incremental changes feed |

Typical entry points:

```python
from googlekit import GoogleKit

client = GoogleKit.auto(services=["gdrive"])
drive = client.drive
```

Or construct the Drive client directly:

```python
from googlekit.gdrive import DriveClient

drive = DriveClient.from_oauth("client_secret.json", token_path="token.json")
```

## Auth & scopes

See also [Authentication](authentication.md) and [Scopes](scopes.md).

### Auto-detect

```python
from googlekit import GoogleKit

client = GoogleKit.auto(services=["gdrive"])
drive = client.drive
```

Order: try ADC → look for credential files in the working directory → raise `AuthenticationError` with guidance.

### OAuth (desktop)

```python
from googlekit import GoogleKit
from googlekit.auth.scopes import ScopeProfile

client = GoogleKit.from_oauth(
    "client_secret.json",
    token_path="token.json",
    services=["gdrive"],
    profile=ScopeProfile.READWRITE,  # default
)
drive = client.drive
```

Or via `DriveClient`:

```python
from googlekit.gdrive import DriveClient
from googlekit.auth.scopes import ScopeProfile

drive = DriveClient.from_oauth(
    "client_secret.json",
    token_path="token.json",
    profile=ScopeProfile.FULL,  # full drive scope when needed
)
```

### Service account

```python
from googlekit.gdrive import DriveClient

drive = DriveClient.from_service_account(
    "service-account.json",
    subject=None,  # set for Workspace domain-wide delegation
)
```

Ordinary service accounts do **not** see a personal user's Drive. Share files/folders with the service-account email, or use domain-wide delegation with `subject`.

### Application Default Credentials

```python
from googlekit.gdrive import DriveClient

drive = DriveClient.from_adc(quota_project_id=None)
```

### Drive scope presets

| `ScopeProfile` | OAuth scope | Typical use |
| -------------- | ----------- | ----------- |
| `metadata` | `drive.metadata.readonly` | List/metadata only |
| `readonly` | `drive.readonly` | Read files without write |
| `readwrite` (default) | `drive.file` | Files created/opened by the app |
| `full` | `drive` | Broad access (empty trash, full My Drive, etc.) |

Prefer `drive.file` (`READWRITE`) when possible. Operations like `empty_trash()` require the full `drive` scope (`ScopeProfile.FULL`).

Custom scopes:

```python
from googlekit.auth.scopes import Scope, ScopeSet
from googlekit.gdrive import DriveClient

drive = DriveClient.from_oauth(
    "client_secret.json",
    scopes=ScopeSet.of(Scope.DRIVE_READONLY),
)
```

## DriveClient

```python
from googlekit.gdrive import DriveClient
from googlekit.core.configuration import ClientConfig
```

### Constructors

| Method | Signature |
| ------ | --------- |
| `from_oauth` | `(client_secrets: str \| Path, token_path: str \| Path \| None = None, scopes: ScopeSet \| list[str] \| None = None, *, profile: ScopeProfile = ScopeProfile.READWRITE, config: ClientConfig \| None = None) -> DriveClient` |
| `from_service_account` | `(credentials_file: str \| Path, subject: str \| None = None, scopes: ScopeSet \| list[str] \| None = None, *, profile: ScopeProfile = ScopeProfile.READWRITE, config: ClientConfig \| None = None) -> DriveClient` |
| `from_adc` | `(quota_project_id: str \| None = None, scopes: ScopeSet \| list[str] \| None = None, *, profile: ScopeProfile = ScopeProfile.READWRITE, config: ClientConfig \| None = None) -> DriveClient` |
| `from_provider` | `(provider: CredentialProvider, *, config: ClientConfig \| None = None) -> DriveClient` |

### Properties

| Property | Type | Description |
| -------- | ---- | ----------- |
| `provider` | `CredentialProvider` | Credential provider in use |
| `config` | `ClientConfig` | Runtime config (timeouts, chunk size, Shared Drive flags, retries) |
| `transport` | `Transport` | HTTP/API transport |
| `files` | `FilesManager` | File operations |
| `folders` | `FoldersManager` | Folder / tree operations |
| `permissions` | `PermissionsManager` | Sharing |
| `changes` | `ChangesManager` | Changes feed |

Via the unified client:

```python
from googlekit import GoogleKit

client = GoogleKit.auto(services=["gdrive"])
drive = client.drive  # DriveClient
```

## Models

Public models from `googlekit.gdrive`:

| Type | Purpose |
| ---- | ------- |
| `DriveFile` | File/folder metadata (`id`, `name`, `mime_type`, checksums, links, `is_folder`, `is_google_native`, …) |
| `DriveFolder` | Folder metadata |
| `Permission` | Sharing permission entry |
| `Change` | One changes-feed entry (`removed`, `file_id`, nested `file`, …) |
| `UploadResult` | `file`, `bytes_uploaded`, `overwritten` |
| `DownloadResult` | `size`, `path`, `mime_type`, `exported`, optional `data` |
| `OverwritePolicy` | `ERROR` / `SKIP` / `OVERWRITE` |
| `PermissionRole` | `owner`, `organizer`, `fileOrganizer`, `writer`, `commenter`, `reader` |

Default metadata field sets used by the managers:

- Files: `id, name, mimeType, parents, size, md5Checksum, …` (`FILE_FIELDS`)
- Permissions: `id, type, role, emailAddress, …` (`PERMISSION_FIELDS`)
- Changes: includes `nextPageToken`, `newStartPageToken`, and nested file fields (`CHANGE_FIELDS`)

## FilesManager

Access: `drive.files`.

Default page size is `100` (`DEFAULT_PAGE_SIZE`). List/search return `Page[DriveFile]`; `iterate` returns a lazy `PageIterator[DriveFile]`.

### list

```python
drive.files.list(
    *,
    query: str | None = None,
    folder_id: str | None = None,
    page_size: int = 100,
    page_token: str | None = None,
    order_by: str | None = None,
    fields: str = FILE_FIELDS,
    corpora: str | None = None,
    drive_id: str | None = None,
    include_trashed: bool = False,
) -> Page[DriveFile]
```

One page of files. Trashed items are excluded unless `include_trashed=True`. When `folder_id` is set, the query includes `'{folder_id}' in parents`.

```python
page = drive.files.list(folder_id="root", page_size=50, order_by="name")
for f in page.items:
    print(f.name, f.id)
if page.has_more:
    next_page = drive.files.list(folder_id="root", page_token=page.next_page_token)
```

Shared Drive listing: pass `drive_id` (sets `corpora="drive"` automatically). `corpora="drive"` without `drive_id` raises `ValidationError`.

### iterate

```python
drive.files.iterate(
    *,
    query: str | None = None,
    folder_id: str | None = None,
    page_size: int = 100,
    page_token: str | None = None,
    order_by: str | None = None,
    fields: str = FILE_FIELDS,
    corpora: str | None = None,
    drive_id: str | None = None,
    include_trashed: bool = False,
) -> PageIterator[DriveFile]
```

Lazily walks all pages:

```python
for f in drive.files.iterate(folder_id="FOLDER_ID"):
    print(f.name)
```

### search

```python
drive.files.search(
    query: str,
    *,
    page_size: int = 100,
    page_token: str | None = None,
    order_by: str | None = None,
    fields: str = FILE_FIELDS,
    corpora: str | None = None,
    drive_id: str | None = None,
) -> Page[DriveFile]
```

Drive query syntax (non-empty `query` required):

```python
page = drive.files.search("name contains 'report' and mimeType = 'application/pdf'")
```

### get

```python
drive.files.get(file_id: str, *, fields: str = FILE_FIELDS) -> DriveFile
```

```python
meta = drive.files.get("FILE_ID")
print(meta.name, meta.mime_type, meta.web_view_link)
```

### create

```python
drive.files.create(
    name: str,
    *,
    mime_type: str = "application/octet-stream",
    parents: list[str] | None = None,
    fields: str = FILE_FIELDS,
    **metadata,
) -> DriveFile
```

Creates metadata (empty binary file or Google-native doc). Extra kwargs are merged into the API body.

```python
doc = drive.files.create(
    "Notes",
    mime_type="application/vnd.google-apps.document",
    parents=["FOLDER_ID"],
)
```

### copy

```python
drive.files.copy(
    file_id: str,
    *,
    name: str | None = None,
    parents: list[str] | None = None,
    fields: str = FILE_FIELDS,
) -> DriveFile
```

```python
copy = drive.files.copy("FILE_ID", name="Report copy", parents=["FOLDER_ID"])
```

### move

```python
drive.files.move(
    file_id: str,
    *,
    add_parents: list[str] | None = None,
    remove_parents: list[str] | None = None,
    fields: str = FILE_FIELDS,
) -> DriveFile
```

Requires `add_parents` and/or `remove_parents` (raises `ValidationError` otherwise):

```python
drive.files.move("FILE_ID", add_parents=["NEW_FOLDER"], remove_parents=["OLD_FOLDER"])
```

### rename

```python
drive.files.rename(file_id: str, name: str, *, fields: str = FILE_FIELDS) -> DriveFile
```

```python
drive.files.rename("FILE_ID", "renamed.pdf")
```

### update_metadata

```python
drive.files.update_metadata(
    file_id: str,
    *,
    fields: str = FILE_FIELDS,
    **metadata,
) -> DriveFile
```

Patches metadata. Accepts snake_case aliases such as `mime_type`, `modified_time`, `drive_id`, `md5_checksum`. At least one field is required.

```python
drive.files.update_metadata("FILE_ID", starred=True, description="Q1 archive")
```

### trash / restore

```python
drive.files.trash(file_id: str, *, fields: str = FILE_FIELDS) -> DriveFile
drive.files.restore(file_id: str, *, fields: str = FILE_FIELDS) -> DriveFile
```

```python
drive.files.trash("FILE_ID")
drive.files.restore("FILE_ID")
```

### empty_trash

```python
drive.files.empty_trash(*, drive_id: str | None = None) -> None
```

Permanently deletes all trashed files for the authenticated user. Requires the full `drive` scope. Pass `drive_id` to empty trash on a Shared Drive.

```python
drive.files.empty_trash()
drive.files.empty_trash(drive_id="SHARED_DRIVE_ID")
```

### delete

```python
drive.files.delete(file_id: str) -> None
```

Permanent delete (cannot be undone):

```python
drive.files.delete("FILE_ID")
```

### find_by_name

```python
drive.files.find_by_name(
    name: str,
    *,
    parents: list[str] | None = None,
    mime_type: str | None = None,
) -> DriveFile | None
```

First non-trashed exact name match under the given parents:

```python
existing = drive.files.find_by_name("report.pdf", parents=["FOLDER_ID"])
```

### upload_path

```python
drive.files.upload_path(
    path: str | Path,
    *,
    parents: list[str] | None = None,
    name: str | None = None,
    mime_type: str | None = None,
    overwrite: OverwritePolicy | str = OverwritePolicy.ERROR,
    chunk_size: int | None = None,
    progress: ProgressCallback | None = None,
    resumable: bool = True,
) -> UploadResult | None
```

Uploads a local file. Returns `None` when `overwrite=SKIP` and a same-named file already exists. MIME is guessed from the path when omitted.

```python
from googlekit.gdrive import OverwritePolicy

result = drive.files.upload_path(
    "report.pdf",
    parents=["FOLDER_ID"],
    overwrite=OverwritePolicy.OVERWRITE,
)
print(result.file.id, result.overwritten)
```

### upload_bytes

```python
drive.files.upload_bytes(
    data: bytes,
    name: str,
    *,
    parents: list[str] | None = None,
    mime_type: str = "application/octet-stream",
    overwrite: OverwritePolicy | str = OverwritePolicy.ERROR,
    chunk_size: int | None = None,
    progress: ProgressCallback | None = None,
) -> UploadResult | None
```

```python
result = drive.files.upload_bytes(
    b"hello",
    name="hello.txt",
    mime_type="text/plain",
    parents=["FOLDER_ID"],
)
```

### upload_fileobj

```python
drive.files.upload_fileobj(
    fileobj: BinaryIO,
    name: str,
    *,
    parents: list[str] | None = None,
    mime_type: str = "application/octet-stream",
    overwrite: OverwritePolicy | str = OverwritePolicy.ERROR,
    chunk_size: int | None = None,
    progress: ProgressCallback | None = None,
    size: int | None = None,
    resumable: bool = True,
) -> UploadResult | None
```

```python
with open("data.bin", "rb") as fh:
    drive.files.upload_fileobj(fh, name="data.bin", parents=["FOLDER_ID"], size=1024)
```

### download_path

```python
drive.files.download_path(
    file_id: str,
    destination: str | Path,
    *,
    chunk_size: int | None = None,
    progress: ProgressCallback | None = None,
    export_format: str | None = None,
) -> DownloadResult
```

Streams to disk (does not buffer the whole file). Google-native files require `export_format` (or use `export()`).

```python
result = drive.files.download_path("FILE_ID", "out/report.pdf")
print(result.path, result.size)
```

### download_bytes

```python
drive.files.download_bytes(
    file_id: str,
    *,
    chunk_size: int | None = None,
    progress: ProgressCallback | None = None,
    export_format: str | None = None,
) -> DownloadResult
```

Loads into memory — prefer `download_path` for large files:

```python
result = drive.files.download_bytes("FILE_ID")
data = result.data
```

### download_fileobj

```python
drive.files.download_fileobj(
    file_id: str,
    fileobj: BinaryIO,
    *,
    chunk_size: int | None = None,
    progress: ProgressCallback | None = None,
    export_format: str | None = None,
) -> DownloadResult
```

```python
with open("out.bin", "wb") as fh:
    drive.files.download_fileobj("FILE_ID", fh)
```

### export

```python
drive.files.export(
    file_id: str,
    export_format: str,
    destination: str | Path | None = None,
    *,
    chunk_size: int | None = None,
    progress: ProgressCallback | None = None,
) -> DownloadResult
```

Exports a Google-native file. Short names (`pdf`, `docx`, `xlsx`, …) or full MIME types are accepted. With `destination=None`, returns bytes in `DownloadResult.data`.

```python
drive.files.export("DOC_ID", "pdf", "notes.pdf")
drive.files.export("SHEET_ID", "xlsx", "data.xlsx")
raw = drive.files.export("DOC_ID", "txt")  # bytes in raw.data
```

## FoldersManager

Access: `drive.folders`.

### create

```python
drive.folders.create(
    name: str,
    *,
    parent_id: str | None = None,
    fields: str = FILE_FIELDS,
) -> DriveFolder
```

```python
folder = drive.folders.create("Reports", parent_id=None)  # My Drive root
```

### create_path

```python
drive.folders.create_path(
    path: str,
    *,
    parent_id: str | None = None,
    fields: str = FILE_FIELDS,
) -> DriveFolder
```

Creates nested folders from a slash-separated path, reusing existing names:

```python
leaf = drive.folders.create_path("Projects/2026/Q1")
print(leaf.id, leaf.name)
```

### list_children

```python
drive.folders.list_children(
    folder_id: str = "root",
    *,
    include_folders: bool = True,
    include_files: bool = True,
    include_trashed: bool = False,
    page_size: int = 100,
) -> list[DriveFile]
```

Eager list of immediate children (use `files.iterate` for lazy pagination):

```python
children = drive.folders.list_children("FOLDER_ID", include_folders=False)
```

### upload_directory

```python
drive.folders.upload_directory(
    local_path: str | Path,
    *,
    parent_id: str | None = None,
    overwrite: OverwritePolicy | str = OverwritePolicy.ERROR,
    progress: ProgressCallback | None = None,
    create_root: bool = True,
) -> DriveFolder
```

Recursively uploads a local directory tree. With `create_root=True` (default), creates a Drive folder named after the local directory. With `create_root=False`, `parent_id` is required and files land directly under that folder. Symlink cycles are skipped.

```python
from googlekit.gdrive import OverwritePolicy

dest = drive.folders.upload_directory(
    "./project",
    parent_id="FOLDER_ID",
    overwrite=OverwritePolicy.SKIP,
)
print(dest.id)
```

### download_directory

```python
drive.folders.download_directory(
    folder_id: str,
    destination: str | Path,
    *,
    overwrite: OverwritePolicy | str = OverwritePolicy.ERROR,
    progress: ProgressCallback | None = None,
    max_depth: int = 50,
) -> Path
```

Recursively downloads a Drive folder. Shortcuts are skipped. Google-native Docs/Sheets/Slides are exported as PDF (`{name}.pdf`) by default. Raises `ValidationError` if `max_depth` is exceeded.

```python
path = drive.folders.download_directory("FOLDER_ID", "./backup")
```

## PermissionsManager

Access: `drive.permissions`.

Roles (`PermissionRole` or string): `owner`, `organizer`, `fileOrganizer`, `writer`, `commenter`, `reader`.

### list

```python
drive.permissions.list(file_id: str, *, fields: str = PERMISSION_FIELDS) -> list[Permission]
```

```python
for p in drive.permissions.list("FILE_ID"):
    print(p.type, p.role, p.email_address)
```

### share_user

```python
drive.permissions.share_user(
    file_id: str,
    email: str,
    *,
    role: PermissionRole | str = PermissionRole.READER,
    notify: bool = True,
    message: str | None = None,
) -> Permission
```

```python
from googlekit.gdrive import PermissionRole

drive.permissions.share_user(
    "FILE_ID",
    "alice@example.com",
    role=PermissionRole.WRITER,
    message="Please review",
)
```

### share_group

```python
drive.permissions.share_group(
    file_id: str,
    email: str,
    *,
    role: PermissionRole | str = PermissionRole.READER,
    notify: bool = True,
    message: str | None = None,
) -> Permission
```

```python
drive.permissions.share_group("FILE_ID", "team@example.com", role="reader")
```

### share_anyone

```python
drive.permissions.share_anyone(
    file_id: str,
    *,
    role: PermissionRole | str = PermissionRole.READER,
    allow_file_discovery: bool = False,
    public: bool = False,
) -> Permission
```

Creates an `anyone` permission. **Requires `public=True`** — without it, raises `ValidationError` to prevent accidental public sharing.

```python
drive.permissions.share_anyone("FILE_ID", role="reader", public=True)
```

### share_domain

```python
drive.permissions.share_domain(
    file_id: str,
    domain: str,
    *,
    role: PermissionRole | str = PermissionRole.READER,
    allow_file_discovery: bool = False,
) -> Permission
```

```python
drive.permissions.share_domain("FILE_ID", "example.com", role="reader")
```

### change_role

```python
drive.permissions.change_role(
    file_id: str,
    permission_id: str,
    role: PermissionRole | str,
) -> Permission
```

```python
drive.permissions.change_role("FILE_ID", "PERMISSION_ID", "writer")
```

### remove

```python
drive.permissions.remove(file_id: str, permission_id: str) -> None
```

```python
drive.permissions.remove("FILE_ID", "PERMISSION_ID")
```

### create_shareable_link

```python
drive.permissions.create_shareable_link(
    file_id: str,
    *,
    role: PermissionRole | str = PermissionRole.READER,
    public: bool = False,
) -> str
```

Ensures an `anyone` permission for the role (if missing) and returns `webViewLink`. **Requires `public=True`.**

```python
link = drive.permissions.create_shareable_link("FILE_ID", public=True)
print(link)
```

## ChangesManager

Access: `drive.changes`. Use for incremental sync.

### get_start_page_token

```python
drive.changes.get_start_page_token(*, drive_id: str | None = None) -> str
```

Save this token before your first sync window. Optional `drive_id` scopes to a Shared Drive.

```python
token = drive.changes.get_start_page_token()
# persist token
```

### list

```python
drive.changes.list(
    page_token: str,
    *,
    page_size: int = 100,
    drive_id: str | None = None,
    include_removed: bool = True,
    fields: str = CHANGE_FIELDS,
) -> Page[Change]
```

One page of changes. When the feed is caught up, the raw response includes `newStartPageToken` (iteration stops; read it from `page.raw`).

```python
page = drive.changes.list(token)
for change in page.items:
    if change.removed:
        print("removed", change.file_id)
    elif change.file:
        print("updated", change.file.name)
```

### iterate

```python
drive.changes.iterate(
    page_token: str,
    *,
    page_size: int = 100,
    drive_id: str | None = None,
    include_removed: bool = True,
    fields: str = CHANGE_FIELDS,
) -> PageIterator[Change]
```

Lazily consumes the feed until exhausted. Persist `newStartPageToken` from the last page's `raw` for the next run (see [Incremental changes](#incremental-changes)).

## Export formats

Short names resolve via `EXPORT_MIME_MAP` in `googlekit.gdrive.export_formats` (official Drive export table).

### Google Docs (`application/vnd.google-apps.document`)

| Short name | MIME type |
| ---------- | --------- |
| `pdf` | `application/pdf` |
| `docx` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `odt` | `application/vnd.oasis.opendocument.text` |
| `rtf` | `application/rtf` |
| `txt` | `text/plain` |
| `html` / `zip` | `application/zip` (HTML export is a zip archive) |
| `epub` | `application/epub+zip` |
| `md` / `markdown` | `text/markdown` |

### Google Sheets (`application/vnd.google-apps.spreadsheet`)

| Short name | MIME type |
| ---------- | --------- |
| `pdf` | `application/pdf` |
| `xlsx` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `ods` | `application/vnd.oasis.opendocument.spreadsheet` |
| `csv` | `text/csv` |
| `tsv` | `text/tab-separated-values` |
| `html` / `zip` | `application/zip` |

### Google Slides (`application/vnd.google-apps.presentation`)

| Short name | MIME type |
| ---------- | --------- |
| `pdf` | `application/pdf` |
| `pptx` | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| `odp` | `application/vnd.oasis.opendocument.presentation` |
| `txt` | `text/plain` |
| `png` | `image/png` |
| `jpeg` / `jpg` | `image/jpeg` |
| `svg` | `image/svg+xml` |

### Drawings (`application/vnd.google-apps.drawing`)

| Short name | MIME type |
| ---------- | --------- |
| `pdf` | `application/pdf` |
| `png` | `image/png` |
| `jpeg` / `jpg` | `image/jpeg` |
| `svg` | `image/svg+xml` |

### Apps Script / Vids

| Source MIME | Short name | Export MIME |
| ----------- | ---------- | ----------- |
| `application/vnd.google-apps.script` | `json` | `application/vnd.google-apps.script+json` |
| `application/vnd.google-apps.vid` | `mp4` | `video/mp4` |

Invalid combinations raise `ValidationError`.

## Shared drives

`ClientConfig.supports_all_drives` defaults to `True`. When enabled, managers send `supportsAllDrives=True`, and list/changes list calls also send `includeItemsFromAllDrives=True`.

```python
from googlekit.core.configuration import ClientConfig
from googlekit.gdrive import DriveClient

drive = DriveClient.from_oauth(
    "client_secret.json",
    config=ClientConfig(supports_all_drives=True),  # default
)

# List files in a Shared Drive
page = drive.files.list(drive_id="SHARED_DRIVE_ID")

# Changes for a Shared Drive
token = drive.changes.get_start_page_token(drive_id="SHARED_DRIVE_ID")
```

Rules:

- Passing `drive_id` to `files.list` / `files.iterate` sets `corpora="drive"` if you omit `corpora`
- `corpora="drive"` without `drive_id` raises `ValidationError`
- `empty_trash(drive_id=...)` empties trash for that Shared Drive

Disable Shared Drive params when you only need My Drive:

```python
drive = DriveClient.from_oauth(
    "client_secret.json",
    config=ClientConfig(supports_all_drives=False),
)
```

## Overwrite policies

`OverwritePolicy` controls name collisions on upload and directory sync:

| Value | Behavior |
| ----- | -------- |
| `ERROR` (default) | Raise `ValidationError` if the destination name already exists |
| `SKIP` | Leave the existing file; upload helpers return `None` |
| `OVERWRITE` | Replace content of the existing Drive file (same id) |

Accepts the enum or string (`"error"`, `"skip"`, `"overwrite"`).

```python
from googlekit.gdrive import OverwritePolicy

drive.files.upload_path("a.pdf", parents=["FOLDER"], overwrite=OverwritePolicy.SKIP)
drive.folders.upload_directory("./data", overwrite="overwrite")
```

For uploads, existence is checked with `find_by_name` under `parents` (or `["root"]` when parents are omitted). For `download_directory`, the policy applies to local paths.

## Progress callbacks

Type: `ProgressCallback = Callable[[int, int | None], None]` — `(bytes_so_far, total_or_None)`.

Default chunk size is `256 * 1024` (256 KiB), overridable via `chunk_size=` or `ClientConfig.chunk_size`.

```python
def on_progress(done: int, total: int | None) -> None:
    if total:
        print(f"{done}/{total} ({100 * done / total:.0f}%)")
    else:
        print(f"{done} bytes")

drive.files.upload_path("large.bin", progress=on_progress)
drive.files.download_path("FILE_ID", "large.bin", progress=on_progress)
```

Callback exceptions are logged and do not abort the transfer.

## Errors

Drive operations use the shared hierarchy documented in [Errors](errors.md):

| Situation | Exception |
| --------- | --------- |
| Bad local input (empty id, missing path, invalid role, `share_anyone` without `public=True`) | `ValidationError` |
| HTTP 404 | `NotFoundError` |
| HTTP 409 / 412 | `ConflictError` |
| HTTP 429 | `RateLimitError` |
| Quota / 403 quota reasons | `QuotaExceededError` |
| Missing OAuth scope | `InsufficientScopesError` |
| Retries exhausted | `RetryExhaustedError` |
| Missing `googleapiclient` extra | `MissingExtraError` |

```python
from googlekit.core.exceptions import ValidationError, NotFoundError

try:
    drive.files.get("missing")
except NotFoundError as exc:
    print(exc.status_code, exc.reason)
```

## Full recipes

### Upload a folder

```python
from googlekit import GoogleKit
from googlekit.gdrive import OverwritePolicy

client = GoogleKit.auto(services=["gdrive"])
drive = client.drive

dest = drive.folders.upload_directory(
    "./project",
    parent_id=None,  # My Drive root
    overwrite=OverwritePolicy.SKIP,
    create_root=True,
)
print("Uploaded to folder", dest.id)
```

Upload into an existing Drive folder without creating a new root folder:

```python
drive.folders.upload_directory(
    "./project",
    parent_id="EXISTING_FOLDER_ID",
    create_root=False,
    overwrite=OverwritePolicy.OVERWRITE,
)
```

### Sync a folder tree both ways

```python
from googlekit import GoogleKit
from googlekit.gdrive import OverwritePolicy

client = GoogleKit.auto(services=["gdrive"])
drive = client.drive

# Local → Drive
drive.folders.upload_directory(
    "./workspace",
    parent_id="REMOTE_FOLDER_ID",
    create_root=False,
    overwrite=OverwritePolicy.OVERWRITE,
)

# Drive → Local (Google Docs/Sheets/Slides become PDF)
drive.folders.download_directory(
    "REMOTE_FOLDER_ID",
    "./workspace-mirror",
    overwrite=OverwritePolicy.OVERWRITE,
)
```

### Create a public link

```python
from googlekit import GoogleKit

client = GoogleKit.auto(services=["gdrive"])
drive = client.drive

uploaded = drive.files.upload_path("report.pdf")
assert uploaded is not None

# Explicit public=True is required (safety guard)
link = drive.permissions.create_shareable_link(uploaded.file.id, public=True)
print(link)

# Or create the anyone permission yourself, then read webViewLink
drive.permissions.share_anyone(uploaded.file.id, role="reader", public=True)
meta = drive.files.get(uploaded.file.id, fields="webViewLink")
print(meta.web_view_link)
```

### Empty trash

Requires `ScopeProfile.FULL` (`https://www.googleapis.com/auth/drive`):

```python
from googlekit.gdrive import DriveClient
from googlekit.auth.scopes import ScopeProfile

drive = DriveClient.from_oauth(
    "client_secret.json",
    profile=ScopeProfile.FULL,
)
drive.files.empty_trash()
```

### Incremental changes

Prefer `ScopeProfile.FULL` or `READONLY` so the feed covers more than app-created files. Persist `newStartPageToken` from the last page's `raw` dict (use `list` in a loop when you need that field; `iterate` does not expose page `raw`).

```python
from pathlib import Path

from googlekit.gdrive import DriveClient
from googlekit.auth.scopes import ScopeProfile

drive = DriveClient.from_oauth("client_secret.json", profile=ScopeProfile.FULL)
token_path = Path("drive_changes_token.txt")

if token_path.exists():
    token = token_path.read_text(encoding="utf-8").strip()
else:
    token = drive.changes.get_start_page_token()
    token_path.write_text(token, encoding="utf-8")

last_raw: dict | None = None
while True:
    page = drive.changes.list(token)
    for change in page.items:
        if change.removed:
            print("deleted", change.file_id)
        elif change.file:
            print("changed", change.file.id, change.file.name)
    last_raw = page.raw
    if not page.next_page_token:
        break
    token = page.next_page_token

new_token = last_raw.get("newStartPageToken") if last_raw else None
if new_token:
    token_path.write_text(str(new_token), encoding="utf-8")
```

### Search, move, and export

```python
from googlekit import GoogleKit

client = GoogleKit.auto(services=["gdrive"])
drive = client.drive

page = drive.files.search("name contains 'Q1' and trashed = false")
for f in page.items:
    if f.is_google_native:
        drive.files.export(f.id, "pdf", f"{f.name}.pdf")
    else:
        archive = drive.folders.create_path("Archive/2026")
        drive.files.move(f.id, add_parents=[archive.id], remove_parents=f.parents)
```

### Share with a teammate and revoke

```python
from googlekit.gdrive import PermissionRole

perm = drive.permissions.share_user(
    "FILE_ID",
    "bob@example.com",
    role=PermissionRole.COMMENTER,
    notify=True,
)
drive.permissions.change_role("FILE_ID", perm.id, PermissionRole.READER)
drive.permissions.remove("FILE_ID", perm.id)
```
