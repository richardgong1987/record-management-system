"""In-window header strip: app logo on the left + title next to it.

Sits above the QTabWidget so the app retains a visible brand mark even
when the OS title bar is suppressed (see MainWindow.__init__).
"""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

_HEADER_ICON_PX = 22


class AppHeaderView(QWidget):
    def __init__(self, title: str, icon_path: Path) -> None:
        super().__init__()
        self.setObjectName("appHeader")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 6, 14, 6)
        layout.setSpacing(8)
        layout.addWidget(self._build_logo(icon_path), alignment=Qt.AlignVCenter)
        layout.addWidget(self._build_title(title), alignment=Qt.AlignVCenter)
        layout.addStretch()

    def _build_logo(self, icon_path: Path) -> QLabel:
        logo = QLabel()
        logo.setObjectName("appLogo")
        pixmap = QIcon(str(icon_path)).pixmap(_HEADER_ICON_PX, _HEADER_ICON_PX)
        logo.setPixmap(pixmap)
        logo.setFixedSize(_HEADER_ICON_PX, _HEADER_ICON_PX)
        return logo

    def _build_title(self, title: str) -> QLabel:
        label = QLabel(title)
        label.setObjectName("appTitle")
        return label
