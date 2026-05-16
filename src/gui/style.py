"""Centralised Qt style sheet for the application.

One QSS string, applied once at startup via :func:`apply_style`.
Individual views set object names on their widgets so the rules below
can target them without coupling QSS strings into widget files.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import QApplication, QLineEdit, QStyle, QWidget

# Palette — single source of truth so future tweaks happen in one place.
COLOR_BG = "#f5f7fa"
COLOR_PANEL = "#ffffff"
COLOR_BORDER = "#d0d7de"
COLOR_TEXT = "#1f2328"
COLOR_MUTED = "#656d76"
COLOR_PRIMARY = "#1f6feb"
COLOR_PRIMARY_HOVER = "#1a5fd1"
COLOR_DANGER = "#cf222e"
COLOR_DANGER_HOVER = "#b21726"
COLOR_HEADER_BG = "#eaeef2"
COLOR_ROW_ALT = "#f6f8fa"
COLOR_SELECTION = "#dbeafe"

STYLE_SHEET = f"""
QMainWindow, QWidget {{
    background-color: {COLOR_BG};
    color: {COLOR_TEXT};
    font-size: 14px;
}}

QGroupBox {{
    background-color: {COLOR_PANEL};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    margin-top: 14px;
    padding: 12px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: {COLOR_TEXT};
}}

QLineEdit, QComboBox {{
    background-color: {COLOR_PANEL};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    padding: 6px 8px;
    min-height: 22px;
}}
QLineEdit:focus, QComboBox:focus {{
    border: 1px solid {COLOR_PRIMARY};
}}

QPushButton {{
    background-color: {COLOR_PANEL};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    padding: 6px 14px;
    min-height: 24px;
    min-width: 80px;
}}
QPushButton:hover {{
    background-color: {COLOR_HEADER_BG};
}}
QPushButton:pressed {{
    background-color: {COLOR_BORDER};
}}

QPushButton#primary {{
    background-color: {COLOR_PRIMARY};
    color: white;
    border: 1px solid {COLOR_PRIMARY};
    font-weight: 600;
}}
QPushButton#primary:hover {{
    background-color: {COLOR_PRIMARY_HOVER};
    border-color: {COLOR_PRIMARY_HOVER};
}}

QPushButton#destructive {{
    background-color: {COLOR_PANEL};
    color: {COLOR_DANGER};
    border: 1px solid {COLOR_DANGER};
}}
QPushButton#destructive:hover {{
    background-color: {COLOR_DANGER};
    color: white;
}}

QTabWidget::pane {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    background-color: {COLOR_PANEL};
    top: -1px;
}}
QTabBar::tab {{
    background-color: {COLOR_BG};
    border: 1px solid {COLOR_BORDER};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 8px 18px;
    margin-right: 2px;
    color: {COLOR_MUTED};
}}
QTabBar::tab:selected {{
    background-color: {COLOR_PANEL};
    color: {COLOR_TEXT};
    font-weight: 600;
}}
QTabBar::tab:hover:!selected {{
    background-color: {COLOR_HEADER_BG};
}}

QTableWidget {{
    background-color: {COLOR_PANEL};
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    gridline-color: {COLOR_BORDER};
    alternate-background-color: {COLOR_ROW_ALT};
    selection-background-color: {COLOR_SELECTION};
    selection-color: {COLOR_TEXT};
}}
QTableWidget::item {{
    padding: 4px 6px;
}}
QHeaderView::section {{
    background-color: {COLOR_HEADER_BG};
    color: {COLOR_TEXT};
    border: none;
    border-right: 1px solid {COLOR_BORDER};
    border-bottom: 1px solid {COLOR_BORDER};
    padding: 8px 6px;
    font-weight: 600;
}}

QStatusBar {{
    background-color: {COLOR_PANEL};
    border-top: 1px solid {COLOR_BORDER};
}}
QStatusBar QLabel#status {{
    font-weight: 600;
    color: {COLOR_TEXT};
    padding: 2px 8px;
}}
QStatusBar QLabel#dataFile {{
    color: {COLOR_MUTED};
    padding: 2px 8px;
}}

QLabel#pageLabel {{
    color: {COLOR_MUTED};
    font-weight: 500;
}}
"""


def apply_style(app: QApplication) -> None:
    """Install the Fusion base style and the app-wide QSS."""
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE_SHEET)


def size_window_to_screen(
    window: QWidget,
    width_ratio: float = 0.85,
    height_ratio: float = 0.80,
) -> None:
    """Resize and centre ``window`` relative to its current screen.

    Falls back to a sensible default when no screen is available
    (headless test environments). Honours the window's minimum size.
    """
    screen = window.screen() or QGuiApplication.primaryScreen()
    if screen is None:
        window.resize(1400, 700)
        return
    geo = screen.availableGeometry()
    width = max(window.minimumWidth(), int(geo.width() * width_ratio))
    height = max(window.minimumHeight(), int(geo.height() * height_ratio))
    window.resize(width, height)
    window.move(
        geo.x() + (geo.width() - width) // 2,
        geo.y() + (geo.height() - height) // 2,
    )


def search_icon() -> QIcon:
    """Best-effort search icon — themed where available, fallback to a
    Qt standard pixmap so the leading position is never empty."""
    icon = QIcon.fromTheme("edit-find")
    if not icon.isNull():
        return icon
    app = QApplication.instance()
    if app is not None:
        return app.style().standardIcon(QStyle.SP_FileDialogContentsView)
    return QIcon()


def decorate_search_input(line_edit: QLineEdit) -> None:
    """Attach the search icon at the leading edge of the input."""
    line_edit.addAction(search_icon(), QLineEdit.LeadingPosition)
    line_edit.setClearButtonEnabled(True)


# Re-exported so call sites don't import Qt just for one constant.
ALIGN_CENTER = Qt.AlignCenter
