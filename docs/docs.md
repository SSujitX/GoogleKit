# Google Docs

Install: `uv add googlekit`

Enable the **Google Docs API**. Export and sharing typically also need the **Drive API**.

## Client

```python
from googlekit import GoogleKit

kit = GoogleKit.from_oauth("client_secret.json", services=["gdocs"])
docs = kit.docs
```

## Managers

| Manager | Role |
| ------- | ---- |
| `docs.documents` | Create, get, batchUpdate, structural inspect |
| `docs.content` | Insert/append/replace text, styles, lists, links |
| `docs.tables` | Insert tables, rows/cols, cell content |
| `docs.images` | Insert/resize images from public URLs |

## Intended API

```python
doc = docs.documents.create("Proposal")
docs.documents.get(doc.id)
docs.content.append_text(doc.id, "Hello")
docs.content.insert_text(doc.id, index=1, text="Title\n")
docs.content.replace_all(doc.id, "{{NAME}}", "Ada")
docs.content.delete_range(doc.id, start=1, end=5)
```

## UTF-16 indexes

The Docs API uses UTF-16 code unit indexes. Python string indexes are **not** always
equal to Docs indexes (especially with emoji and non-BMP characters). GoogleKit
helpers account for this; document any index math carefully in application code.

## Cross-service

- Export via Drive (`export` MIME types)
- Share via Drive permissions
- Request Drive scopes explicitly when using those helpers
