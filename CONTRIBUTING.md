# Contributing to GoogleKit

Thanks for your interest in contributing. GoogleKit is an unofficial community SDK
for Google Workspace APIs. It is not affiliated with Google.

## Development setup

Use [uv](https://docs.astral.sh/uv/) exclusively:

```bash
uv sync --group dev
uv run pytest -m "not integration"
uv build
```

Python **3.11–3.14** are supported targets. Local development should use a version
supported by current dependencies (see `.python-version`).

## Project layout

- `src/googlekit/` — library code (`auth`, `core`, and service packages)
- `tests/unit/` — mocked unit tests (no network)
- `tests/integration/` — live API tests (skipped by default)
- `tests/packaging/` — install / wheel checks
- `docs/` — MkDocs documentation
- `examples/` — short runnable samples with placeholder IDs

## Coding guidelines

- Prefer small, focused modules and typed public APIs
- Do not log secrets (tokens, client secrets, private keys)
- Never commit credential or token files
- Raise actionable errors (`MissingExtraError` suggests `uv add googlekit` if clients are missing)
- Unit tests must not hit the network; inject sleep for retry tests

## Pull requests

1. Keep changes focused and documented when behavior changes
2. Add or update unit tests for new behavior
3. Ensure `uv run pytest -m "not integration"` passes locally
4. Do not include secrets, tokens, or real user data in examples

## Integration tests

Integration tests are marked `@pytest.mark.integration` and are disabled by default.
They require explicit environment configuration and never use committed credentials.
See each placeholder under `tests/integration/*/`.

## Maintainer: publishing to PyPI

End-user docs do **not** cover releases. Maintainers use this section + [`AGENT.md`](AGENT.md) + [`RELEASE.md`](RELEASE.md).

Pushing a version tag (`v*`) runs [`.github/workflows/publish.yml`](.github/workflows/publish.yml):

1. Unit tests (`pytest -m "not integration"`)
2. Tag must match `version` in `pyproject.toml` (e.g. `v0.0.2` ↔ `0.0.2`)
3. `uv build` (wheel + sdist)
4. Smoke-import the wheel
5. Publish to PyPI via [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC — no API token in the repo)
6. Create a GitHub Release from the matching `## [X.Y.Z]` section in `RELEASE.md`, and attach dist artifacts

### Release steps

1. Write `## [X.Y.Z] - YYYY-MM-DD` in [`RELEASE.md`](RELEASE.md)
2. Set `version = "X.Y.Z"` in `pyproject.toml` (keep `USER_AGENT` in sync)
3. Commit on `main` / `master`
4. Tag and push:

```bash
git tag v0.0.2
git push origin v0.0.2
```

Do not create the GitHub Release by hand unless the workflow failed.

### Trusted Publishing

Pending publisher (first time / new project): [pypi.org account Publishing](https://pypi.org/manage/account/publishing/)

- Project: `googlekit`
- Owner: `SSujitX`
- Repository: `GoogleKit`
- Workflow: `publish.yml`
- Environment: leave empty

See [Creating a project through OIDC](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/). A pending publisher does not reserve the name until the first upload.

Optional one-time manual: `uv build && uv publish` with a token, then switch to Trusted Publishing.

### Local build only

```bash
uv build
```

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
