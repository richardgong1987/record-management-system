from dataclasses import dataclass

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from conf.loader import load_config
from gui.styles import SPACING
from record import (
    RecordValidationError,
    check_unique_id,
    create_record,
    load_records,
    save_records,
)
from gui.airline.controller import AirlineFormController
from gui.common.dialogs import confirm
from gui.airline.types import AIRLINE_TEXT_FIELDS
from gui.airline.view import AirlineFormView
from gui.client.controller import ClientFormController
from gui.client.types import CLIENT_TEXT_FIELDS
from gui.client.view import ClientFormView
from gui.flight.controller import FlightFormController
from gui.flight.types import FLIGHT_TEXT_FIELDS
from gui.flight.view import FlightFormView
from gui.record_list.controller import RecordListController
from gui.record_list.view import RecordListView
from gui.status_bar.view import StatusBarView
from gui.tab.controller import TabController
from gui.tab.view import TabView
from shared.utils.pagination import Page, paginate

# Configuration is read once at module import. Tests that need different
# paths still monkeypatch the module-level constants below.
_CONFIG = load_config()
APP_TITLE = _CONFIG.name
APP_ICON_PATH = _CONFIG.icon_path
DATA_FILE_PATH = _CONFIG.record_file
_WINDOW = _CONFIG.window
_HEADER_ICON_PX = 22

# Per record type: (form view class, form controller class, table columns).
# Add a new key to introduce a new tab — the rest is wired automatically.
_RECORD_TYPES = {
    "Client": (
        ClientFormView,
        ClientFormController,
        CLIENT_TEXT_FIELDS,
    ),
    "Airline": (
        AirlineFormView,
        AirlineFormController,
        AIRLINE_TEXT_FIELDS,
    ),
    "Flight": (FlightFormView, FlightFormController, FLIGHT_TEXT_FIELDS),
}


@dataclass
class _Tab:
    record_type: str
    label: str
    view: TabView
    controller: TabController


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        # Flow:
        # 1. Build per-record-type tabs (form + record list + tab controller)
        # 2. Compose the central QTabWidget from the tabs
        # 3. Mount the two-cell status bar with the data-file path
        # 4. Wire each tab controller's signals to status-bar feedback
        super().__init__()

        # Title is rendered in the in-window header strip, so the OS title bar
        # stays blank. Cmd-Tab / taskbar labelling still uses the application
        # name set via QApplication.setApplicationName in main.py.
        self.setWindowTitle("")
        self._apply_responsive_size()
        self._records = load_records(DATA_FILE_PATH)
        self._page_by_type: dict[str, int] = {rt: 1 for rt in _RECORD_TYPES}
        # The record dict currently selected in each tab. Storing the
        # reference (not an absolute index) keeps selection stable across
        # list rewrites in other tabs and is identity-safe when two records
        # have identical field values (e.g. duplicate Flights).
        self._selected_record_by_type: dict[str, dict | None] = {
            rt: None for rt in _RECORD_TYPES
        }

        # Step 1: Build tabs
        self._tabs: list[_Tab] = [self._build_tab(rt) for rt in _RECORD_TYPES]
        self._tabs_by_type: dict[str, _Tab] = {t.record_type: t for t in self._tabs}

        # Step 2: Compose central QTabWidget
        self.setCentralWidget(self._compose_central())

        # Step 3: Mount status bar
        self.status = StatusBarView()
        self.status.set_data_file(DATA_FILE_PATH)
        self.setStatusBar(self.status)

        # Step 4: Wire signals
        for tab in self._tabs:
            self._connect_tab_signals(tab.controller)

        self._refresh_all_tables()

    def _apply_responsive_size(self) -> None:
        geometry = self._available_geometry()
        if geometry is None:
            self.resize(_WINDOW.fallback_width, _WINDOW.fallback_height)
            return
        width = max(
            _WINDOW.min_width,
            min(
                int(geometry.width() * _WINDOW.preferred_width_ratio), _WINDOW.max_width
            ),
        )
        height = max(
            _WINDOW.min_height,
            min(
                int(geometry.height() * _WINDOW.preferred_height_ratio),
                _WINDOW.max_height,
            ),
        )
        self.resize(width, height)
        self.setMinimumSize(
            min(_WINDOW.min_width, geometry.width() - _WINDOW.screen_padding),
            min(_WINDOW.min_height, geometry.height() - _WINDOW.screen_padding),
        )
        frame = self.frameGeometry()
        frame.moveCenter(geometry.center())
        self.move(frame.topLeft())

    def _available_geometry(self) -> QRect | None:
        screen = self.screen() or QApplication.primaryScreen()
        return screen.availableGeometry() if screen else None

    def _build_tab(self, record_type: str) -> _Tab:
        form_cls, ctrl_cls, columns = _RECORD_TYPES[record_type]
        form = form_cls()
        form_ctrl = ctrl_cls(form)
        record_list = RecordListView(columns)
        list_ctrl = RecordListController(record_list)
        view = TabView(form, record_list)
        controller = TabController(form_ctrl, list_ctrl, record_type)
        return _Tab(
            record_type=record_type,
            label=f"{record_type} Records",
            view=view,
            controller=controller,
        )

    def _compose_central(self) -> QWidget:
        tabs = QTabWidget()
        for tab in self._tabs:
            tabs.addTab(tab.view, tab.label)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_header())
        # Give the tab bar room to breathe below the header — without this
        # the QTabWidget tabs sit flush against the header's bottom border.
        layout.addSpacing(SPACING.header_to_tabs_gap)
        layout.addWidget(tabs, stretch=1)
        return container

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("appHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(14, 6, 14, 6)
        layout.setSpacing(8)
        layout.addWidget(self._build_logo(), alignment=Qt.AlignVCenter)
        title = QLabel(APP_TITLE)
        title.setObjectName("appTitle")
        layout.addWidget(title, alignment=Qt.AlignVCenter)
        layout.addStretch()
        return header

    def _build_logo(self) -> QLabel:
        logo = QLabel()
        logo.setObjectName("appLogo")
        pixmap = QIcon(str(APP_ICON_PATH)).pixmap(_HEADER_ICON_PX, _HEADER_ICON_PX)
        logo.setPixmap(pixmap)
        logo.setFixedSize(_HEADER_ICON_PX, _HEADER_ICON_PX)
        return logo

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

    def _on_create(self, record_type: str, payload: dict) -> None:
        try:
            record = create_record(record_type, payload)
            check_unique_id(record, self._records)
        except RecordValidationError as exc:
            self.status.set_status(str(exc))
            return

        self._records.append(record)
        try:
            save_records(DATA_FILE_PATH, self._records)
        except OSError as exc:
            # Roll back the in-memory append so _records stays consistent
            # with the on-disk file when persistence fails.
            self._records.pop()
            self.status.set_status(f"Save failed: {exc}")
            return

        self._refresh_all_tables()
        self.status.set_status(f"Create {record_type}: {record}")

    def _on_record_selected(self, record_type: str, row_index: int) -> None:
        page = self._visible_page(record_type)
        if not 0 <= row_index < len(page.rows):
            return
        # Store the dict reference directly: two records with identical
        # values (e.g. duplicate Flights) stay distinguishable by identity.
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

    def _on_update(self, record_type: str, payload: dict) -> None:
        selected = self._selected_record(record_type)
        if selected is None:
            self.status.set_status("Select a record to update first.")
            return

        try:
            record = create_record(record_type, payload)
            # Uniqueness is checked against OTHER records (identity-filtered)
            # so a no-op ID edit still succeeds.
            others = [r for r in self._records if r is not selected]
            check_unique_id(record, others)
        except RecordValidationError as exc:
            self.status.set_status(str(exc))
            return

        body = f"Update this {record_type} record?\n\n{record}"
        if not confirm(self, "Confirm update", body):
            self.status.set_status("Update cancelled.")
            return

        new_records = [record if r is selected else r for r in self._records]
        try:
            save_records(DATA_FILE_PATH, new_records)
        except OSError as exc:
            # Keep self._records pointing at the previous list so in-memory
            # state never moves ahead of the on-disk file.
            self.status.set_status(f"Save failed: {exc}")
            return

        self._records = new_records
        self._selected_record_by_type[record_type] = record
        self._refresh_all_tables()
        self.status.set_status(f"Update {record_type}: {record}")

    def _on_delete(self, record_type: str, _payload: dict) -> None:
        # Delete keys off the stored selection, not the form payload, so an
        # edited-but-not-saved form cannot influence which row is removed.
        record = self._selected_record(record_type)
        if record is None:
            self.status.set_status("Select a record to delete first.")
            return

        body = f"Delete this {record_type} record?\n\n{record}"
        if not confirm(self, "Confirm delete", body):
            self.status.set_status("Delete cancelled.")
            return

        # Capture the table-row position via identity so two identical-valued
        # records (e.g. duplicate Flights) stay distinguishable.
        type_records = self._records_for_type(record_type)
        position_in_type = next(i for i, r in enumerate(type_records) if r is record)

        new_records = [r for r in self._records if r is not record]
        try:
            save_records(DATA_FILE_PATH, new_records)
        except OSError as exc:
            self.status.set_status(f"Save failed: {exc}")
            return

        self._records = new_records
        self._refresh_all_tables()
        self._reselect_after_delete(record_type, position_in_type)
        self.status.set_status(f"Delete {record_type}: {record}")

    def _reselect_after_delete(self, record_type: str, deleted_position: int) -> None:
        survivors = self._records_for_type(record_type)
        tab = self._tabs_by_type[record_type]
        if not survivors:
            self._selected_record_by_type[record_type] = None
            tab.view.form.clear()
            return

        new_position = min(deleted_position, len(survivors) - 1)
        new_record = survivors[new_position]
        self._selected_record_by_type[record_type] = new_record
        tab.view.form.populate(new_record)

    def _on_clear_all(self, record_type: str) -> None:
        if not self._records_for_type(record_type):
            self.status.set_status(f"No {record_type} records to clear.")
            return
        body = f"Delete ALL {record_type} records?\n\nThis cannot be undone."
        if not confirm(self, "Confirm clear all", body):
            self.status.set_status("Clear cancelled.")
            return

        # Other-type records keep their dict identity through this filter, so
        # other tabs' selections remain valid without an explicit rebase.
        new_records = [r for r in self._records if r["Type"] != record_type]
        try:
            save_records(DATA_FILE_PATH, new_records)
        except OSError as exc:
            self.status.set_status(f"Save failed: {exc}")
            return

        self._records = new_records
        self._selected_record_by_type[record_type] = None
        self._tabs_by_type[record_type].view.form.clear()
        self._refresh_all_tables()
        self.status.set_status(f"Cleared all {record_type} records.")

    def _on_search(self, record_type: str, query: str) -> None:
        self.status.set_status(f"Search {record_type}: {query!r}")

    def _on_show_all(self, record_type: str) -> None:
        self.status.set_status(f"Show all {record_type}")

    def _step_page(self, record_type: str, delta: int) -> None:
        self._page_by_type[record_type] += delta
        self._refresh_tab(self._tabs_by_type[record_type])

    def _records_for_type(self, record_type: str) -> list[dict]:
        return [record for record in self._records if record["Type"] == record_type]

    def _refresh_all_tables(self) -> None:
        for tab in self._tabs:
            self._refresh_tab(tab)

    def _refresh_tab(self, tab: _Tab) -> None:
        self._paint(tab, self._visible_page(tab.record_type))

    def _visible_page(self, record_type: str) -> Page:
        rows = self._records_for_type(record_type)
        page = paginate(rows, self._page_by_type[record_type])
        self._page_by_type[record_type] = page.current_page
        return page

    def _paint(self, tab: _Tab, page: Page) -> None:
        tab.view.record_list.set_rows(page.rows)
        tab.view.record_list.set_page_label(page.current_page, page.total_pages)
