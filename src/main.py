import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from conf.loader import load_config
from gui.main_window import MainWindow
from gui.styles import apply_app_style


def main() -> int:
    config = load_config()
    app = QApplication(sys.argv)
    app.setApplicationName(config.name)
    app.setWindowIcon(QIcon(str(config.icon_path)))
    apply_app_style(app)
    win = MainWindow()
    win.show()
    win.raise_()
    win.activateWindow()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
