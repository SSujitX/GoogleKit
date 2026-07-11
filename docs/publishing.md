---
title: Publish GoogleKit to PyPI
description: >-
  Build and publish GoogleKit with uv, Trusted Publishing, SemVer, and the
  release checklist for maintainers.
---

# Publishing

GoogleKit is published with [uv](https://docs.astral.sh/uv/) and semantic versioning.

**Related:** [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) ·
[PyPI project](https://pypi.org/project/googlekit/) ·
[RELEASE.md](https://github.com/SSujitX/GoogleKit/blob/master/RELEASE.md)

## Build locally

```bash
uv build
```

Artifacts appear under `dist/` (wheel + sdist).

## Trusted Publishing (recommended)

The repository workflow `.github/workflows/publish.yml` publishes on version tags
(`v*`) using PyPI **Trusted Publishing**. No PyPI API tokens are stored in the repo.

Requirements on PyPI:

1. Create a pending publisher for the project
2. Point it at this GitHub repository and the `publish.yml` workflow
3. Leave the GitHub Environment field empty (or create an environment and add it to the workflow later)

Push a tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

The workflow runs `uv build` then `uv publish` with `id-token: write`.

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
- Follow [SemVer](https://semver.org/): `MAJOR.MINOR.PATCH`

## Checklist before a release

- [ ] Changelog updated
- [ ] `uv run pytest -m "not integration"`
- [ ] `uv build` succeeds
- [ ] Wheel installs cleanly and `import googlekit` works
