# pylint: skip-file
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication


@dataclass(frozen=True)
class Spacing:
    """Layout-spacing tokens shared by QSS and Qt layout calls.

    Keeping these in one place stops the same magic number from drifting in
    QSS, contentsMargins, and addSpacing calls.

    Panel padding is owned by QSS (QGroupBox padding-* rules). View layouts
    therefore zero their own contentsMargins to avoid stacking with QSS.
    """

    panel_margin_top: int = 22  # QGroupBox margin-top — slot for title
    panel_padding_top: int = 18  # QGroupBox padding-top — gap from border to first row
    panel_padding_side: int = 14  # QGroupBox padding left/right
    panel_padding_bottom: int = 14  # QGroupBox padding-bottom
    title_left: int = 16  # title horizontal offset from panel edge
    title_h_padding: int = 12  # horizontal padding inside title label
    title_v_padding: int = 4  # vertical padding inside title label
    row_spacing: int = 12  # vertical gap between rows inside a panel
    field_v_spacing: int = 10  # vertical gap between form rows
    field_h_spacing: int = 12  # horizontal gap between label and field
    button_spacing: int = 8  # gap between CRUD buttons
    button_min_width: int = 84  # minimum CRUD button width
    tab_outer_margin: int = 12  # tab page left/right/bottom margin
    tab_top_padding: int = 15  # tab page top margin — gap from tab bar to content
    tab_outer_spacing: int = 12  # gap between form panel and record list
    header_to_tabs_gap: int = 15  # vertical gap between the app header and the tab bar


SPACING = Spacing()

# Global stylesheet that drags Qt's default look toward the agreed mockup
# (see docs/design/option3.png). Spacing values come from SPACING so the same
# tokens drive both QSS and layout-margin calls in view modules.
_APP_STYLESHEET = f"""
QWidget {{
    color: #1F2933;
    background-color: #ECEEF1;
    font-family: "Segoe UI", "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
    font-size: 11pt;
}}

QMainWindow, QDialog {{
    background-color: #ECEEF1;
}}

QWidget#appHeader {{
    background: #FFFFFF;
    border-bottom: 1px solid #D8DBE0;
}}
QLabel#appLogo {{
    background: transparent;
}}
QLabel#appTitle {{
    color: #1F2933;
    font-size: 13pt;
    font-weight: 600;
    background: transparent;
}}

QTabWidget::pane {{
    border: 1px solid #D8DBE0;
    background: #FFFFFF;
    top: -1px;
}}
QTabWidget::tab-bar {{
    left: 8px;
}}
QTabBar::tab {{
    background: #ECEEF1;
    color: #52606D;
    border: 1px solid #D8DBE0;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 7px 18px;
    margin-right: 2px;
    min-width: 110px;
}}
QTabBar::tab:hover:!selected {{
    background: #E2E8EE;
}}
QTabBar::tab:selected {{
    background: #FFFFFF;
    color: #1F2933;
    font-weight: 600;
    border-bottom: 2px solid #3D8BFD;
    margin-bottom: -1px;
}}

QGroupBox {{
    background: #FFFFFF;
    border: 1px solid #D0D7DE;
    border-radius: 8px;
    margin-top: {SPACING.panel_margin_top}px;
    padding: {SPACING.panel_padding_top}px {SPACING.panel_padding_side}px {SPACING.panel_padding_bottom}px {SPACING.panel_padding_side}px;
    font-size: 12pt;
    font-weight: 600;
    color: #1F2933;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: {SPACING.title_left}px;
    padding: {SPACING.title_v_padding}px {SPACING.title_h_padding}px;
    background-color: #FFFFFF;
    color: #1F2933;
    font-weight: 600;
}}

QLabel {{
    background: transparent;
}}

QLineEdit, QComboBox {{
    background: #FFFFFF;
    border: 1px solid #D8DBE0;
    border-radius: 4px;
    padding: 5px 8px;
    selection-background-color: #C8DBF7;
    selection-color: #1F2933;
    min-height: 22px;
}}
QLineEdit:focus, QComboBox:focus {{
    border: 1px solid #3D8BFD;
}}
QLineEdit:disabled, QComboBox:disabled {{
    background: #F4F5F7;
    color: #9AA5B1;
}}
QComboBox::drop-down {{
    width: 22px;
    border-left: 1px solid #D8DBE0;
}}
QComboBox QAbstractItemView {{
    background: #FFFFFF;
    border: 1px solid #D8DBE0;
    selection-background-color: #C8DBF7;
    selection-color: #1F2933;
    outline: none;
}}

QPushButton {{
    background: #FFFFFF;
    color: #1F2933;
    border: 1px solid #C9CFD7;
    border-radius: 4px;
    padding: 6px 14px;
    min-width: 78px;
    font-weight: 500;
}}
QPushButton:hover {{
    background: #F0F4F8;
    border-color: #B6BEC9;
}}
QPushButton:pressed {{
    background: #E2E8EE;
}}
QPushButton:disabled {{
    color: #9AA5B1;
    background: #F4F5F7;
    border-color: #E2E5EA;
}}
QPushButton#primary {{
    background: #3D8BFD;
    color: #FFFFFF;
    border-color: #3074DC;
}}
QPushButton#primary:hover {{
    background: #2F7AE5;
    border-color: #265FB8;
}}
QPushButton#primary:pressed {{
    background: #2768C7;
}}

QHeaderView::section {{
    background: #E6EEF7;
    color: #1F2933;
    padding: 8px 10px;
    border: none;
    border-right: 1px solid #D8DBE0;
    border-bottom: 1px solid #D8DBE0;
    font-weight: 600;
}}
QHeaderView::section:last {{
    border-right: none;
}}
QTableWidget {{
    background: #FFFFFF;
    alternate-background-color: #F8FAFC;
    gridline-color: #ECEEF1;
    border: 1px solid #D8DBE0;
    border-radius: 4px;
    selection-background-color: #C8DBF7;
    selection-color: #1F2933;
}}
QTableWidget::item {{
    padding: 4px 6px;
    border: none;
}}
QTableCornerButton::section {{
    background: #E6EEF7;
    border: none;
    border-right: 1px solid #D8DBE0;
    border-bottom: 1px solid #D8DBE0;
}}

QStatusBar {{
    background: #ECEEF1;
    border-top: 1px solid #D8DBE0;
    color: #52606D;
}}
QStatusBar::item {{
    border: none;
}}
QStatusBar QLabel {{
    color: #52606D;
    padding: 2px 8px;
}}

QScrollBar:vertical {{
    background: #ECEEF1;
    width: 12px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: #C9CFD7;
    border-radius: 6px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: #B6BEC9;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: #ECEEF1;
    height: 12px;
    margin: 0;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: #C9CFD7;
    border-radius: 6px;
    min-width: 24px;
}}
QScrollBar::handle:horizontal:hover {{
    background: #B6BEC9;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}
"""


def apply_app_style(app: QApplication) -> None:
    """Apply the consolidated QSS stylesheet to the running app."""
    app.setStyle("Fusion")
    app.setStyleSheet(_APP_STYLESHEET)


def search_icon(size: int = 16) -> QIcon:
    """Return a small magnifier icon drawn programmatically.

    Drawn in code (rather than shipped as an asset) so the GUI ships with
    no binary blobs. Stays crisp at the typical 16 px header size.
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor("#52606D"))
    pen.setWidth(2)
    painter.setPen(pen)
    margin = 2
    diameter = size - margin * 2 - 4
    painter.drawEllipse(margin, margin, diameter, diameter)
    handle_x = margin + diameter - 1
    handle_y = margin + diameter - 1
    painter.drawLine(handle_x, handle_y, size - 2, size - 2)
    painter.end()
    return QIcon(pixmap)
