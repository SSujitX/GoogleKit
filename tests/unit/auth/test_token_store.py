"""Token store unit tests."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from googlekit.auth.token_store import (
    FileTokenStore,
    InMemoryTokenStore,
    default_token_path,
    user_config_token_path,
)
from googlekit.core.exceptions import ConfigurationError


def test_in_memory_token_store_roundtrip() -> None:
    store = InMemoryTokenStore()
    assert store.load() is None
    store.save('{"token": "x"}')
    assert store.load() == '{"token": "x"}'
    store.clear()
    assert store.load() is None


def test_file_token_store_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "token.json"
    store = FileTokenStore(path)
    assert store.load() is None
    store.save('{"refresh_token": "redacted"}')
    assert path.exists()
    assert store.load() == '{"refresh_token": "redacted"}'
    store.clear()
    assert not path.exists()


def test_file_token_store_chmod_oserror_ignored(tmp_path: Path) -> None:
    path = tmp_path / "token.json"
    store = FileTokenStore(path)
    with patch("googlekit.auth.token_store.os.chmod", side_effect=OSError("denied")):
        store.save("{}")
    assert store.load() == "{}"


def test_default_token_path_is_cwd_token_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    path = default_token_path()
    assert path == tmp_path / "token.json"


def test_user_config_token_path_uses_platform_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if os.name == "nt":
        monkeypatch.setenv("APPDATA", str(tmp_path))
    else:
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    path = user_config_token_path("googlekit")
    assert path == tmp_path / "googlekit" / "token.json"
    assert path.parent.is_dir()


def test_user_config_token_path_mkdir_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if os.name == "nt":
        monkeypatch.setenv("APPDATA", str(tmp_path))
    else:
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    with patch.object(Path, "mkdir", side_effect=OSError("fail")):
        with pytest.raises(ConfigurationError, match="Cannot create config"):
            user_config_token_path("googlekit")
