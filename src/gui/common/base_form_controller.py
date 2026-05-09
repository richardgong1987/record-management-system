from typing import Generic, TypeVar

from PySide6.QtCore import QObject, Signal

from gui.common.base_form_view import BaseFormView

T = TypeVar("T", bound=BaseFormView)


class BaseFormController(QObject, Generic[T]):
    create_requested = Signal(dict)
    update_requested = Signal(dict)
    delete_requested = Signal(dict)

    def __init__(self, view: T) -> None:
        super().__init__()
        self._view = view
        self._view.create_btn.clicked.connect(self._on_create)
        self._view.update_btn.clicked.connect(self._on_update)
        self._view.delete_btn.clicked.connect(self._on_delete)
        self._view.clear_btn.clicked.connect(self._view.clear)

    def _on_create(self) -> None:
        self.create_requested.emit(self._view.read_payload())

    def _on_update(self) -> None:
        self.update_requested.emit(self._view.read_payload())

    def _on_delete(self) -> None:
        self.delete_requested.emit(self._view.read_payload())
