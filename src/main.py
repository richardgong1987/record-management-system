import sys

from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow
from gui.style import apply_style


def main() -> int:
    app = QApplication(sys.argv)
    apply_style(app)
    win = MainWindow()
    win.show()
    win.raise_()
    win.activateWindow()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
