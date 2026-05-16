from pathlib import Path

from PySide6.QtWidgets import QFrame, QLabel, QStatusBar

# src/gui/status_bar/view.py → project root is four levels up.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]


class StatusBarView(QStatusBar):
    def __init__(self) -> None:
        super().__init__()
        self.setSizeGripEnabled(False)
        self._status_lbl = QLabel("Status: Ready")
        self._status_lbl.setObjectName("status")
        self._data_file_lbl = QLabel()
        self._data_file_lbl.setObjectName("dataFile")
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #D8DBE0;")
        self.addWidget(self._status_lbl, stretch=1)
        self.addPermanentWidget(separator)
        self.addPermanentWidget(self._data_file_lbl)

    def set_status(self, message: str) -> None:
        self._status_lbl.setText(f"Status: {message}")

    def set_data_file(self, path: Path) -> None:
        self._data_file_lbl.setText(f"Data file: {_display_path(path)}")


def _display_path(path: Path) -> str:
    # Show a relative path when the file lives under the project root, so the
    # status bar stays readable on long absolute paths.
    try:
        return str(Path(path).resolve().relative_to(_PROJECT_ROOT))
    except ValueError:
        return str(path)
