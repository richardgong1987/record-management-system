"""Modal dialog helpers shared across GUI features.

Thin wrappers around ``QMessageBox`` so orchestrators do not import Qt
dialog APIs directly. Centralising the wrapper here also gives tests a
single monkey-patch point — ``monkeypatch.setattr("gui.main_window.confirm",
…)`` — instead of stubbing an instance method on each window under test.
"""

from PySide6.QtWidgets import QMessageBox, QWidget


def confirm(parent: QWidget | None, title: str, body: str) -> bool:
    # Default button is No so an accidental Enter never confirms a
    # destructive action (delete, clear-all, etc.).
    reply = QMessageBox.question(
        parent,
        title,
        body,
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No,
    )
    return reply == QMessageBox.Yes
