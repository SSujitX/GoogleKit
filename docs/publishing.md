---
title: Publish GoogleKit to PyPI
description: >-
  Build and publish GoogleKit with uv, Trusted Publishing, SemVer, GitHub Releases,
  and the release checklist for maintainers.
---

# Publishing

GoogleKit is published with [uv](https://docs.astral.sh/uv/) and semantic versioning.

**Related:** [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) ·
[PyPI project](https://pypi.org/project/googlekit/) ·
[RELEASE.md](https://github.com/SSujitX/GoogleKit/blob/master/RELEASE.md)

## What a tag does

Pushing a version tag (`v*`) runs [`.github/workflows/publish.yml`](https://github.com/SSujitX/GoogleKit/blob/master/.github/workflows/publish.yml):

1. Unit tests (`pytest -m "not integration"`)
2. Checks the tag matches `version` in `pyproject.toml` (e.g. `v0.1.0` ↔ `0.1.0`)
3. Builds wheel + sdist (`uv build`)
4. Smoke-imports the wheel
5. Publishes to **PyPI** (Trusted Publishing — no API token in the repo)
6. Creates a **GitHub Release** with notes from `RELEASE.md` for that version, and attaches the wheel + sdist

This is a **Python package** release (`.whl` / `.tar.gz`), not a Windows `.exe` pipeline.

## Release checklist

1. Move items from `## [Unreleased]` into a new `## [X.Y.Z] - YYYY-MM-DD` section in [`RELEASE.md`](https://github.com/SSujitX/GoogleKit/blob/master/RELEASE.md)
2. Set `version = "X.Y.Z"` in `pyproject.toml`
3. Commit on `main` / `master`
4. Tag and push:

```bash
git tag v0.1.0
git push origin v0.1.0
```

Do **not** create the GitHub Release by hand unless the workflow failed — the action owns it.

## Build locally

```bash
uv build
```

Artifacts appear under `dist/` (wheel + sdist).

## Trusted Publishing (required for PyPI)

Requirements on PyPI:

1. Create a pending publisher for the project
2. Point it at this GitHub repository and the `publish.yml` workflow
3. Leave the GitHub Environment field empty (or create an environment and add it to the workflow later)

## TestPyPI

For a dry run, configure a TestPyPI trusted publisher similarly, or run:

```bash
uv build
uv publish --publish-url https://test.pypi.org/legacy/
```

Prefer Trusted Publishing over long-lived tokens.

## Versioning

- Version is defined once in `pyproject.toml`
- Runtime version comes from package metadata (`importlib.metadata`)
- Tag must be `v` + that version (`v0.1.0`)
- Follow [SemVer](https://semver.org/): `MAJOR.MINOR.PATCH`

## Checklist before a release

- [ ] `RELEASE.md` section for this version filled in
- [ ] `pyproject.toml` version bumped
- [ ] `uv run pytest -m "not integration"`
- [ ] `uv build` succeeds
- [ ] Tag `vX.Y.Z` pushed
