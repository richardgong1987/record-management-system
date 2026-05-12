from PySide6.QtCore import QObject, Signal

from gui.record_list.controller import RecordListController


class TabController(QObject):
    create_requested = Signal(str, dict)
    update_requested = Signal(str, dict)
    delete_requested = Signal(str, dict)
    search_requested = Signal(str, str)
    show_all_requested = Signal(str)
    page_changed = Signal(str, int)

    def __init__(
        self, form_ctrl: QObject, list_ctrl: RecordListController, record_type: str
    ) -> None:
        super().__init__()
        self._record_type = record_type
        self._form_ctrl = form_ctrl
        self._list_ctrl = list_ctrl
        self._wire_form_signals()
        self._wire_list_signals()

    def _wire_form_signals(self) -> None:
        rt = self._record_type
        self._form_ctrl.create_requested.connect(
            lambda p: self.create_requested.emit(rt, p)
        )
        self._form_ctrl.update_requested.connect(
            lambda p: self.update_requested.emit(rt, p)
        )
        self._form_ctrl.delete_requested.connect(
            lambda p: self.delete_requested.emit(rt, p)
        )

    def _wire_list_signals(self) -> None:
        rt = self._record_type
        self._list_ctrl.search_requested.connect(
            lambda q: self.search_requested.emit(rt, q)
        )
        self._list_ctrl.show_all_requested.connect(
            lambda: self.show_all_requested.emit(rt)
        )
        self._list_ctrl.page_changed.connect(lambda p: self.page_changed.emit(rt, p))

    def set_current_page(self, page: int) -> None:
        self._list_ctrl.set_current_page(page)
