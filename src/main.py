import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow
from gui.styles import apply_app_style

APP_ICON_PATH = Path(__file__).resolve().parent / "icons" / "favorite.png"


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Record Management System")
    app.setWindowIcon(QIcon(str(APP_ICON_PATH)))
    apply_app_style(app)
    win = MainWindow()
    win.show()
    win.raise_()
    win.activateWindow()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
