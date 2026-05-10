from PySide6.QtCore import QObject, Signal

from gui.record_list.view import RecordListView


class RecordListController(QObject):
    search_requested = Signal(str)
    show_all_requested = Signal()
    page_changed = Signal(int)

    def __init__(self, view: RecordListView) -> None:
        super().__init__()
        self._view = view
        self._current_page = 1
        self._view.search_btn.clicked.connect(self._on_search)
        self._view.show_all_btn.clicked.connect(self.show_all_requested)
        self._view.prev_btn.clicked.connect(self._on_prev)
        self._view.next_btn.clicked.connect(self._on_next)

    def set_current_page(self, page: int) -> None:
        # Consumer calls this once it knows the displayed page,
        # so prev/next compute correct neighbours.
        self._current_page = max(1, page)

    def _on_search(self) -> None:
        # Step 1: Read query from view
        query = self._view.current_query()
        # Step 2: Emit normalized intent
        self.search_requested.emit(query)

    def _on_prev(self) -> None:
        target = max(1, self._current_page - 1)
        self._current_page = target
        self.page_changed.emit(target)

    def _on_next(self) -> None:
        target = self._current_page + 1
        self._current_page = target
        self.page_changed.emit(target)
