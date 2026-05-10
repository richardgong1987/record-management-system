from pathlib import Path

from PySide6.QtWidgets import QLabel, QStatusBar


class StatusBarView(QStatusBar):
    def __init__(self) -> None:
        super().__init__()
        self._status_lbl = QLabel("Status: Ready")
        self._data_file_lbl = QLabel()
        self.addWidget(self._status_lbl, stretch=1)
        self.addPermanentWidget(self._data_file_lbl)

    def set_status(self, message: str) -> None:
        self._status_lbl.setText(f"Status: {message}")

    def set_data_file(self, path: Path) -> None:
        self._data_file_lbl.setText(f"Data file: {path}")
