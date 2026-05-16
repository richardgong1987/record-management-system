"""Screen-aware window sizing.

Centralises the "size and centre the window against the current screen"
logic so MainWindow stays focused on composition. The helper falls back to
fixed dimensions when no screen is reachable (headless tests, broken DPI).
"""

from PySide6.QtCore import QRect
from PySide6.QtWidgets import QApplication, QMainWindow

from conf.loader import WindowConfig


def apply_responsive_size(window: QMainWindow, sizing: WindowConfig) -> None:
    """Resize, set the minimum, and centre `window` against the active screen."""
    geometry = _available_geometry(window)
    if geometry is None:
        window.resize(sizing.fallback_width, sizing.fallback_height)
        return
    width = max(
        sizing.min_width,
        min(int(geometry.width() * sizing.preferred_width_ratio), sizing.max_width),
    )
    height = max(
        sizing.min_height,
        min(int(geometry.height() * sizing.preferred_height_ratio), sizing.max_height),
    )
    window.resize(width, height)
    window.setMinimumSize(
        min(sizing.min_width, geometry.width() - sizing.screen_padding),
        min(sizing.min_height, geometry.height() - sizing.screen_padding),
    )
    frame = window.frameGeometry()
    frame.moveCenter(geometry.center())
    window.move(frame.topLeft())


def _available_geometry(window: QMainWindow) -> QRect | None:
    screen = window.screen() or QApplication.primaryScreen()
    return screen.availableGeometry() if screen else None
