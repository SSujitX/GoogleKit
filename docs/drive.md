# Google Drive

Install: `uv add "googlekit[gdrive]"`

Enable the **Google Drive API** in Google Cloud Console.

## Client

```python
from googlekit import GoogleKit
# or: from googlekit.gdrive import DriveClient

kit = GoogleKit.from_oauth("client_secret.json", services=["gdrive"])
drive = kit.drive
```

## Managers

| Manager | Role |
| ------- | ---- |
| `drive.files` | Upload, download, search, metadata, trash/delete |
| `drive.folders` | Create folders/paths, recursive directory transfer |
| `drive.permissions` | Share, roles, links |
| `drive.changes` | Change feed / sync |

## Intended files API

```python
drive.files.list(page_size=100, q="mimeType='application/pdf'")
drive.files.iterate(q=None)          # lazy pagination
drive.files.search("name contains 'report'")
drive.files.get(file_id)
drive.files.create(name, parents=None, mime_type=None)
drive.files.upload(path, parents=None, resumable=True)
drive.files.upload_bytes(data, name, ...)
drive.files.download(file_id, path)
drive.files.download_bytes(file_id)
drive.files.export(file_id, mime_type)  # Google-native files
drive.files.copy(file_id, name=None)
drive.files.move(file_id, new_parent_id)
drive.files.rename(file_id, name)
drive.files.update_metadata(file_id, **fields)
drive.files.trash(file_id)
drive.files.restore(file_id)
drive.files.delete(file_id)          # permanent
```

Upload modes: simple, multipart, and resumable (configurable chunk size and progress callback).
Large downloads stream; they do not load entire files into memory unless requested.

## Folders & permissions

```python
drive.folders.create("Reports", parent_id=None)
drive.folders.create_path("a/b/c")
drive.folders.list_children(folder_id)
drive.folders.upload_tree(local_dir, parent_id)
drive.folders.download_tree(folder_id, local_dir)

drive.permissions.list(file_id)
drive.permissions.share_user(file_id, email, role="reader")
drive.permissions.share_group(file_id, group_email, role="reader")
drive.permissions.create_link(file_id, role="reader")  # explicit only
drive.permissions.remove(file_id, permission_id)
```

## Shared Drives

Operations that need Shared Drive support pass `supportsAllDrives` (enabled by default
via `ClientConfig.supports_all_drives`). Use corpora / drive ID options where the API requires them.

## Scopes

Prefer `drive.file` for app-owned files. Use `drive.readonly` or full `drive` only when needed.
See [scopes](scopes.md).
