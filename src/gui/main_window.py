from dataclasses import dataclass

from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget

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

CLIENT_COLUMNS = ["ID", "Name", "Phone Number", "City"]
AIRLINE_COLUMNS = ["ID", "Company Name"]
FLIGHT_COLUMNS = ["Client_ID", "Airline_ID", "Date", "Start City", "End City"]


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

        # Step 1: Build tabs
        self._tabs: list[_Tab] = [
            self._build_client_tab(),
            self._build_airline_tab(),
            self._build_flight_tab(),
        ]

        # Step 2: Compose central QTabWidget
        self.setCentralWidget(self._compose_central())

        # Step 3: Mount status bar
        self.status = StatusBarView()
        self.status.set_data_file(DATA_FILE_PATH)
        self.setStatusBar(self.status)

        # Step 4: Wire signals
        for tab in self._tabs:
            self._connect_tab_signals(tab.controller)

    def _build_client_tab(self) -> _Tab:
        form = ClientFormView()
        form_ctrl = ClientFormController(form)
        return self._build_tab("Client Records", "Client", form, form_ctrl, CLIENT_COLUMNS)

    def _build_airline_tab(self) -> _Tab:
        form = AirlineFormView()
        form_ctrl = AirlineFormController(form)
        return self._build_tab("Airline Records", "Airline", form, form_ctrl, AIRLINE_COLUMNS)

    def _build_flight_tab(self) -> _Tab:
        form = FlightFormView()
        form_ctrl = FlightFormController(form)
        return self._build_tab("Flight Records", "Flight", form, form_ctrl, FLIGHT_COLUMNS)

    def _build_tab(self, label, record_type, form, form_ctrl, columns) -> _Tab:
        record_list = RecordListView(columns)
        list_ctrl = RecordListController(record_list)
        view = TabView(form, record_list)
        controller = TabController(form_ctrl, list_ctrl, record_type)
        # Keep references so the controllers aren't garbage collected.
        view._form_ctrl = form_ctrl
        view._list_ctrl = list_ctrl
        return _Tab(label=label, view=view, controller=controller)

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
        self.status.set_status(f"Create {record_type}: {payload}")

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
