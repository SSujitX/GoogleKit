"""Wheel contents and metadata checks (in-repo / after uv build)."""

from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / "dist"


def _latest_wheel() -> Path | None:
    if not DIST.exists():
        return None
    wheels = sorted(DIST.glob("googlekit-*.whl"))
    return wheels[-1] if wheels else None


def _latest_sdist() -> Path | None:
    if not DIST.exists():
        return None
    sdists = sorted(DIST.glob("googlekit-*.tar.gz"))
    return sdists[-1] if sdists else None


@pytest.fixture(scope="module")
def wheel_path() -> Path:
    existing = _latest_wheel()
    if existing is not None:
        return existing
    pytest.importorskip("hatchling")
    import subprocess
    import sys

    subprocess.run(
        [sys.executable, "-m", "uv", "build"],
        cwd=ROOT,
        check=True,
    )
    built = _latest_wheel()
    if built is None:
        pytest.skip("uv build did not produce a wheel")
    return built


def test_wheel_contains_py_typed(wheel_path: Path) -> None:
    with zipfile.ZipFile(wheel_path) as zf:
        names = zf.namelist()
    assert any(n.endswith("googlekit/py.typed") for n in names)
    assert any(n.endswith("googlekit/__init__.py") for n in names)
    assert any("googlekit/auth/" in n for n in names)
    assert any("googlekit/core/" in n for n in names)


def test_wheel_excludes_secrets(wheel_path: Path) -> None:
    with zipfile.ZipFile(wheel_path) as zf:
        basenames = {Path(n).name.lower() for n in zf.namelist()}
    assert "token.json" not in basenames
    assert ".env" not in basenames
    assert not any(n.startswith("client_secret") and n.endswith(".json") for n in basenames)
    assert not any(n.startswith("service_account") and n.endswith(".json") for n in basenames)


def test_wheel_metadata_has_name(wheel_path: Path) -> None:
    with zipfile.ZipFile(wheel_path) as zf:
        meta_files = [n for n in zf.namelist() if n.endswith("METADATA")]
        assert meta_files
        meta = zf.read(meta_files[0]).decode("utf-8")
    assert "Name: googlekit" in meta
    assert "License: MIT" in meta or "License-Expression: MIT" in meta


def test_sdist_includes_license_when_built() -> None:
    sdist = _latest_sdist()
    if sdist is None:
        pytest.skip("no sdist in dist/; run uv build first")
    with tarfile.open(sdist, "r:gz") as tf:
        names = tf.getnames()
    assert any(n.endswith("LICENSE") for n in names)
    assert any("pyproject.toml" in n for n in names)
