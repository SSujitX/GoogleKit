## [0.0.2] - 2026-07-12

Documentation and maintainer tooling release. No breaking API changes to the library surface.

### Changed

#### Authentication docs (README + docs site)

- All three auth methods (ADC, service account, OAuth) now share the same **Step 1–2** flow: create a Cloud project, then **Step 2: Enable APIs**
- Step 2 links to [APIs & Services → Library](https://console.cloud.google.com/apis/library) plus direct enable links for Drive, Sheets, Calendar, Docs, and Slides
- OAuth Method 3 updated for Google’s **Google Auth Platform** UI:
  - [Branding](https://console.cloud.google.com/auth/branding)
  - [Audience](https://console.cloud.google.com/auth/audience) (test users)
  - [Data Access](https://console.cloud.google.com/auth/scopes)
  - [Clients](https://console.cloud.google.com/auth/clients) → **+ Create client** → **Desktop app**
- Older **APIs & Services → Credentials / OAuth consent screen** path documented as a fallback
- `docs/authentication.md` official-links and Cloud Console setup summary aligned with the same Auth Platform flow

#### Versioning (single source of truth)

- Package version is read only from `pyproject.toml` metadata via `importlib.metadata`
- `googlekit.__version__`, CLI `--version`, and default `USER_AGENT` (`googlekit/<version>`) all use `package_version()` — **no hardcoded release versions in source**
- Fallback when the package is not installed: `"dev"`
- Release habit: bump `pyproject.toml` → update this file → `uv sync` → tag `vX.Y.Z`

#### Docs site & maintainer docs

- Removed public MkDocs page `/publishing/` (`docs/publishing.md` deleted; dropped from `mkdocs.yml` nav and home map)
- Publishing / Trusted Publishing / tag checklist moved into [`CONTRIBUTING.md`](CONTRIBUTING.md) (maintainer section)
- [`AGENT.md`](AGENT.md) rewritten as the current architecture / LLM reference (auth rules, service quirks, CI/publish, agent do-nots) — replaces the old greenfield “build GoogleKit” prompt

#### CI / release workflow

- Publish workflow `run-name` is now `PyPI publish ${{ github.ref_name }}` (e.g. `PyPI publish v0.0.2`) instead of the latest commit subject

### Added

- `package_version()` in `src/googlekit/core/constants.py` as the shared version helper
- Maintainer publishing section in `CONTRIBUTING.md` (tag steps, pending Trusted Publisher fields, local `uv build`)

### Removed

- `docs/publishing.md` and the **Publishing** entry from the public documentation site
