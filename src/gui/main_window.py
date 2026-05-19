from dataclasses import dataclass

from PySide6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from conf.loader import load_config
from gui.common.dialogs import confirm
from gui.header.view import AppHeaderView
from gui.status_bar.view import StatusBarView
from gui.styles import SPACING
from gui.tab.controller import TabController
from gui.tab_registry import RECORD_TYPES, Tab, build_tab
from gui.window_sizing import apply_responsive_size
from record import load_records, save_records, search_records
from record.use_cases import (
    Cancelled,
    ClearAllRecords,
    CreateRecord,
    DeleteRecord,
    Err,
    Ok,
    Result,
    State,
    UpdateRecord,
)
from shared.utils.pagination import Page, paginate

# Configuration is read once at module import. Tests that need different
# paths still monkeypatch the module-level constants below.
_CONFIG = load_config()
APP_TITLE = _CONFIG.name
APP_ICON_PATH = _CONFIG.icon_path
DATA_FILE_PATH = _CONFIG.record_file
_WINDOW = _CONFIG.window


@dataclass(frozen=True)
class _UseCases:
    # Bundle the four mutating use cases so MainWindow stays under pylint's
    # ``max-attributes`` and the slots all reach them through one handle.
    create: CreateRecord
    update: UpdateRecord
    delete: DeleteRecord
    clear_all: ClearAllRecords


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        # Flow:
        # 1. Load records + per-tab view state
        # 2. Construct use cases with save + confirm ports
        # 3. Build per-record-type tabs and compose the central QTabWidget
        # 4. Mount status bar and wire signals
        super().__init__()
        self.setWindowTitle("")
        apply_responsive_size(self, _WINDOW)

        # Step 1: View state
        self._records = load_records(DATA_FILE_PATH)
        self._page_by_type: dict[str, int] = {rt: 1 for rt in RECORD_TYPES}
        # Latched on Search click, not on keystroke; empty disables the filter.
        self._query_by_type: dict[str, str] = {rt: "" for rt in RECORD_TYPES}
        # Stored as the dict reference (not an index) so two records with
        # identical field values (e.g. duplicate Flights) stay distinguishable
        # and so list rewrites in other tabs don't shift it.
        self._selected_record_by_type: dict[str, dict | None] = {
            rt: None for rt in RECORD_TYPES
        }

        # Step 2: Use cases
        self._uc = self._build_use_cases()

        # Step 3: Tabs + central widget
        self._tabs: list[Tab] = [build_tab(rt) for rt in RECORD_TYPES]
        self._tabs_by_type: dict[str, Tab] = {t.record_type: t for t in self._tabs}
        self.setCentralWidget(self._compose_central())

        # Step 4: Status bar + signal wiring
        self.status = StatusBarView()
        self.status.set_data_file(DATA_FILE_PATH)
        self.setStatusBar(self.status)
        for tab in self._tabs:
            self._connect_tab_signals(tab.controller)

        self._refresh_all_tables()

    def _build_use_cases(self) -> _UseCases:
        # Ports are closures over module-level ``save_records`` / ``confirm``
        # so that tests monkeypatching those names take effect on every call.
        def save(records: list[dict]) -> None:
            save_records(DATA_FILE_PATH, records)

        def ask(title: str, body: str) -> bool:
            return confirm(self, title, body)

        return _UseCases(
            create=CreateRecord(save=save),
            update=UpdateRecord(save=save, confirm=ask),
            delete=DeleteRecord(save=save, confirm=ask),
            clear_all=ClearAllRecords(save=save, confirm=ask),
        )

# -------------------------- UI Construction --------------------------

    def _compose_central(self) -> QWidget:
        tabs = QTabWidget()
        for tab in self._tabs:
            tabs.addTab(tab.view, tab.label)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(AppHeaderView(APP_TITLE, APP_ICON_PATH))
        # Give the tab bar room to breathe below the header — without this
        # the QTabWidget tabs sit flush against the header's bottom border.
        layout.addSpacing(SPACING.header_to_tabs_gap)
        layout.addWidget(tabs, stretch=1)
        return container

    def _connect_tab_signals(self, ctrl: TabController) -> None:
        ctrl.create_requested.connect(self._on_create)
        ctrl.update_requested.connect(self._on_update)
        ctrl.delete_requested.connect(self._on_delete)
        ctrl.clear_all_requested.connect(self._on_clear_all)
        ctrl.search_requested.connect(self._on_search)
        ctrl.show_all_requested.connect(self._on_show_all)
        ctrl.prev_requested.connect(lambda rt: self._step_page(rt, -1))
        ctrl.next_requested.connect(lambda rt: self._step_page(rt, +1))
        ctrl.record_selected.connect(self._on_record_selected)

    # -- Use-case slots --------------------------------------------------

    def _on_create(self, record_type: str, payload: dict) -> None:
        self._apply(
            record_type, self._uc.create(record_type, payload, self._state(record_type))
        )

    def _on_update(self, record_type: str, payload: dict) -> None:
        self._apply(
            record_type, self._uc.update(record_type, payload, self._state(record_type))
        )

    def _on_delete(self, record_type: str, payload: dict) -> None:
        self._apply(
            record_type, self._uc.delete(record_type, payload, self._state(record_type))
        )

    def _on_clear_all(self, record_type: str) -> None:
        self._apply(
            record_type, self._uc.clear_all(record_type, self._state(record_type))
        )

    def _state(self, record_type: str) -> State:
        return State(self._records, self._selected_record(record_type))

    def _apply(self, record_type: str, result: Result) -> None:
        # Single rendering point for every mutating use case. Err / Cancelled
        # are status-only; Ok swaps in-memory state AFTER the use case has
        # already persisted, so disk and memory cannot drift apart.
        match result:
            case Err(message=msg) | Cancelled(message=msg):
                self.status.set_status(msg)
            case Ok(
                new_records=records,
                new_selection=selection,
                message=msg,
                repaint_form=repaint,
            ):
                self._records = records
                self._selected_record_by_type[record_type] = selection
                if repaint:
                    self._repaint_form(record_type, selection)
                self._refresh_all_tables()
                self.status.set_status(msg)

    def _repaint_form(self, record_type: str, selection: dict | None) -> None:
        form = self._tabs_by_type[record_type].view.form
        if selection is None:
            form.clear()
        else:
            form.populate(selection)

    # -------------------------- Selection helpers --------------------------

    def _on_record_selected(self, record_type: str, row_index: int) -> None:
        page = self._visible_page(record_type)
        if not 0 <= row_index < len(page.rows):
            return
        selected = page.rows[row_index]
        self._selected_record_by_type[record_type] = selected
        self._tabs_by_type[record_type].view.form.populate(selected)

    def _selected_record(self, record_type: str) -> dict | None:
        # Return None for a stale selection — the dict may have been removed
        # by clear-all or a programmatic mutation; identity check, not ==.
        record = self._selected_record_by_type.get(record_type)
        if record is None or not any(r is record for r in self._records):
            return None
        return record

# -------------------------- Search / pagination --------------------------
    def _on_search(self, record_type: str, query: str) -> None:
        self._query_by_type[record_type] = query
        self._reset_page(record_type)
        self._refresh_record_type(record_type)
        matches = len(search_records(self._records, record_type, query))
        self.status.set_status(
            f"Search {record_type}: {query!r} — {matches} match(es)."
        )

    def _on_show_all(self, record_type: str) -> None:
        self._query_by_type[record_type] = ""
        self._reset_page(record_type)
        # Keep the visible search box in sync with the (cleared) query state.
        self._tabs_by_type[record_type].view.record_list.search_input.clear()
        self._refresh_record_type(record_type)
        self.status.set_status(f"Show all {record_type}.")
    def _reset_page(self, record_type: str) -> None:
        self._page_by_type[record_type] = 1

    def _step_page(self, record_type: str, delta: int) -> None:
        self._page_by_type[record_type] += delta
        self._refresh_record_type(record_type)

# -------------------------- Table rendering --------------------------
    def _refresh_all_tables(self) -> None:
        for tab in self._tabs:
            self._refresh_tab(tab)

    def _refresh_record_type(self, record_type: str) -> None:
        self._refresh_tab(self._tabs_by_type[record_type])

    def _refresh_tab(self, tab: Tab) -> None:
        self._paint(tab, self._visible_page(tab.record_type))

    def _visible_page(self, record_type: str) -> Page:
        rows = search_records(
            self._records, record_type, self._query_by_type[record_type]
        )
        page = paginate(rows, self._page_by_type[record_type])
        self._page_by_type[record_type] = page.current_page
        return page

    def _paint(self, tab: Tab, page: Page) -> None:
        tab.view.record_list.set_rows(page.rows)
        tab.view.record_list.set_page_label(page.current_page, page.total_pages)