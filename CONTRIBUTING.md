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

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
