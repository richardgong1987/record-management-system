from PySide6.QtCore import QObject, Signal

from gui.record_list.view import RecordListView


class RecordListController(QObject):
    search_requested = Signal(str)
    show_all_requested = Signal()
    prev_requested = Signal()
    next_requested = Signal()

    def __init__(self, view: RecordListView) -> None:
        super().__init__()
        self._view = view
        self._view.search_btn.clicked.connect(self._on_search)
        self._view.show_all_btn.clicked.connect(self.show_all_requested)
        self._view.prev_btn.clicked.connect(self.prev_requested)
        self._view.next_btn.clicked.connect(self.next_requested)

    def _on_search(self) -> None:
        self.search_requested.emit(self._view.current_query())
