from dataclasses import dataclass

from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget

from data.records import (
    RecordValidationError,
    create_record,
    load_records,
    save_records,
)
from gui.airline.controller import AirlineFormController
from gui.airline.view import AirlineFormView
from gui.client.controller import ClientFormController
from gui.client.view import ClientFormView
from gui.flight.controller import FlightFormController
from gui.flight.view import FlightFormView
from gui.record_list.controller import RecordListController
from gui.record_list.view import RecordListView
from gui.status_bar.view import StatusBarView
from gui.tab.controller import TabController
from gui.tab.view import TabView

DATA_FILE_PATH = "src/record/record.jsonl"

# Per record type: (form view class, form controller class, table columns).
# Add a new key to introduce a new tab — the rest is wired automatically.
_RECORD_TYPES = {
    "Client": (
        ClientFormView,
        ClientFormController,
        ["ID", "Name", "Phone Number", "City"],
    ),
    "Airline": (
        AirlineFormView,
        AirlineFormController,
        ["ID", "Company Name"],
    ),
    "Flight": (
        FlightFormView,
        FlightFormController,
        ["Client_ID", "Airline_ID", "Date", "Start City", "End City"],
    ),
}


@dataclass
class _Tab:
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
        self.setWindowTitle("Record Management System")
        self.resize(1200, 700)
        self.setMinimumSize(1000, 600)
        self._records = load_records(DATA_FILE_PATH)

        # Step 1: Build tabs
        self._tabs: list[_Tab] = [self._build_tab(rt) for rt in _RECORD_TYPES]

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

    def _build_tab(self, record_type: str) -> _Tab:
        form_cls, ctrl_cls, columns = _RECORD_TYPES[record_type]
        form = form_cls()
        form_ctrl = ctrl_cls(form)
        record_list = RecordListView(columns)
        list_ctrl = RecordListController(record_list)
        view = TabView(form, record_list)
        controller = TabController(form_ctrl, list_ctrl, record_type)
        return _Tab(label=f"{record_type} Records", view=view, controller=controller)

    def _compose_central(self) -> QWidget:
        tabs = QTabWidget()
        for tab in self._tabs:
            tabs.addTab(tab.view, tab.label)
        return tabs

    def _connect_tab_signals(self, ctrl: TabController) -> None:
        ctrl.create_requested.connect(self._on_create)
        ctrl.update_requested.connect(self._on_update)
        ctrl.delete_requested.connect(self._on_delete)
        ctrl.search_requested.connect(self._on_search)
        ctrl.show_all_requested.connect(self._on_show_all)
        ctrl.page_changed.connect(self._on_page_changed)

    def _on_create(self, record_type: str, payload: dict) -> None:
        try:
            record = create_record(record_type, payload)
        except RecordValidationError as exc:
            self.status.set_status(str(exc))
            return

        self._records.append(record)
        save_records(DATA_FILE_PATH, self._records)
        self._refresh_all_tables()

        self.status.set_status(f"Create {record_type}: {record}")

    def _on_update(self, record_type: str, payload: dict) -> None:
        self.status.set_status(f"Update {record_type}: {payload}")

    def _on_delete(self, record_type: str, payload: dict) -> None:
        self.status.set_status(f"Delete {record_type}: {payload}")

    def _on_search(self, record_type: str, query: str) -> None:
        self.status.set_status(f"Search {record_type}: {query!r}")

    def _on_show_all(self, record_type: str) -> None:
        self.status.set_status(f"Show all {record_type}")

    def _on_page_changed(self, record_type: str, page: int) -> None:
        self.status.set_status(f"{record_type} → page {page}")

    def _records_for_type(self, record_type: str) -> list[dict]:
        return [record for record in self._records if record["Type"] == record_type]

    def _refresh_all_tables(self) -> None:
        for record_type in _RECORD_TYPES:
            rows = self._records_for_type(record_type)
            for tab in self._tabs:
                if tab.label == f"{record_type} Records":
                    tab.view.record_list.set_rows(rows)
