"""Token persistence backends."""

from __future__ import annotations

import contextlib
import os
import stat
import tempfile
from pathlib import Path

from googlekit.core.exceptions import ConfigurationError


class FileTokenStore:
    """Store OAuth tokens as JSON on disk with restrictive permissions."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> str | None:
        if not self.path.exists():
            return None
        return self.path.read_text(encoding="utf-8")

    def save(self, token_json: str) -> None:
        """Atomically write the token file with mode ``0600`` when supported."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = token_json.encode("utf-8")
        fd, tmp_name = tempfile.mkstemp(
            dir=str(self.path.parent),
            prefix=f".{self.path.name}.",
            suffix=".tmp",
        )
        tmp_path = Path(tmp_name)
        try:
            # fchmod is POSIX-only; Windows has no os.fchmod.
            fchmod = getattr(os, "fchmod", None)
            if fchmod is not None:
                with contextlib.suppress(OSError):
                    fchmod(fd, stat.S_IRUSR | stat.S_IWUSR)
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                with contextlib.suppress(OSError):
                    os.fsync(handle.fileno())
            os.replace(tmp_path, self.path)
            with contextlib.suppress(OSError):
                os.chmod(self.path, stat.S_IRUSR | stat.S_IWUSR)
        except Exception:
            with contextlib.suppress(OSError):
                tmp_path.unlink(missing_ok=True)
            raise

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()


class InMemoryTokenStore:
    """Ephemeral token store for tests and short-lived processes."""

    def __init__(self) -> None:
        self._data: str | None = None

    def load(self) -> str | None:
        return self._data

    def save(self, token_json: str) -> None:
        self._data = token_json

    def clear(self) -> None:
        self._data = None


def default_token_path(app_name: str = "googlekit") -> Path:
    """Return an OS-appropriate user config path for OAuth tokens."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        base = Path(xdg) if xdg else Path.home() / ".config"
    path = base / app_name / "token.json"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ConfigurationError(f"Cannot create config directory: {path.parent}") from exc
    return path
