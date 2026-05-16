"""Application configuration: read once at startup.

Centralises the runtime values previously hard-coded in main.py and
main_window.py (data file path, icon path, app title, window sizing).

Path resolution differs between running from source and running from a
PyInstaller bundle:

- Bundled (read-only) assets — `config.json`, the app icon — are resolved
  against the bundle's extraction directory (`sys._MEIPASS`) when frozen.
- The records file is user data and must remain writable across launches,
  so when frozen we route it to `~/RecordManagementSystem/` regardless of
  the relative path stored in `config.json`. The `_MEIPASS` directory is
  re-extracted on every launch — writing there would silently lose data.

When running from source, both kinds of asset resolve relative to `src/`
exactly as before, so tests and `python src/main.py` are unaffected.
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path

_FROZEN = bool(getattr(sys, "frozen", False))

# Read-only assets: inside _MEIPASS when frozen, src/ otherwise.
_BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))

# Writable user-data root used in frozen mode for record.jsonl.
_USER_DATA_ROOT = Path.home() / "RecordManagementSystem"

# config.json ships inside the bundle in both modes.
if _FROZEN:
    _CONFIG_PATH = _BUNDLE_ROOT / "conf" / "config.json"
else:
    _CONFIG_PATH = Path(__file__).resolve().parent / "config.json"


@dataclass(frozen=True)
class WindowConfig:
    preferred_width_ratio: float
    preferred_height_ratio: float
    max_width: int
    max_height: int
    min_width: int
    min_height: int
    fallback_width: int
    fallback_height: int
    screen_padding: int


@dataclass(frozen=True)
class AppConfig:
    name: str
    icon_path: Path
    record_file: Path
    window: WindowConfig


def load_config() -> AppConfig:
    raw = json.loads(_CONFIG_PATH.read_text())
    app = raw["app"]
    data = raw["data"]
    return AppConfig(
        name=app["name"],
        icon_path=_resolve_bundle(app["icon_path"]),
        record_file=_resolve_record_file(data["record_file"]),
        window=WindowConfig(**raw["window"]),
    )


def _resolve_bundle(rel: str) -> Path:
    return (_BUNDLE_ROOT / rel).resolve()


def _resolve_record_file(rel: str) -> Path:
    # Frozen bundles can't store user data inside _MEIPASS — route the
    # record file to the user's home dir so writes survive across launches.
    if _FROZEN:
        path = _USER_DATA_ROOT / Path(rel).name
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    return (_BUNDLE_ROOT / rel).resolve()
