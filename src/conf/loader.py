"""Application configuration: read once at startup.

Centralises the runtime values previously hard-coded in main.py and
main_window.py (data file path, icon path, app title, window sizing). All
paths in `config.json` are interpreted relative to `src/` so the same file
works from the repo root, a packaged bundle, or a test sandbox.
"""

import json
from dataclasses import dataclass
from pathlib import Path

# src/conf/loader.py → src/ is parents[1].
_SRC_ROOT = Path(__file__).resolve().parents[1]
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
        icon_path=_resolve(app["icon_path"]),
        record_file=_resolve(data["record_file"]),
        window=WindowConfig(**raw["window"]),
    )


def _resolve(rel: str) -> Path:
    # Paths in config.json are stored relative to src/ so they survive
    # packaging and don't bake in absolute developer-machine paths.
    return (_SRC_ROOT / rel).resolve()
