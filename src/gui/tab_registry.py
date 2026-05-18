"""Per-record-type wiring: registry + tab factory.

Lives outside MainWindow so adding a new record type does not require
touching the main window — drop a new entry into RECORD_TYPES and the
factory wires the rest.
"""

from dataclasses import dataclass

from gui.airline.controller import AirlineFormController
from gui.airline.types import AIRLINE_TEXT_FIELDS
from gui.airline.view import AirlineFormView
from gui.client.controller import ClientFormController
from gui.client.types import CLIENT_TABLE_COLUMNS
from gui.client.view import ClientFormView
from gui.flight.controller import FlightFormController
from gui.flight.types import FLIGHT_TEXT_FIELDS
from gui.flight.view import FlightFormView
from gui.record_list.controller import RecordListController
from gui.record_list.view import RecordListView
from gui.tab.controller import TabController
from gui.tab.view import TabView

# Per record type: (form view class, form controller class, table columns).
RECORD_TYPES = {
    "Client": (ClientFormView, ClientFormController, CLIENT_TABLE_COLUMNS),
    "Airline": (AirlineFormView, AirlineFormController, AIRLINE_TEXT_FIELDS),
    "Flight": (FlightFormView, FlightFormController, FLIGHT_TEXT_FIELDS),
}


@dataclass
class Tab:
    record_type: str
    label: str
    view: TabView
    controller: TabController


def build_tab(record_type: str) -> Tab:
    form_cls, ctrl_cls, columns = RECORD_TYPES[record_type]
    form = form_cls()
    form_ctrl = ctrl_cls(form)
    record_list = RecordListView(columns)
    list_ctrl = RecordListController(record_list)
    view = TabView(form, record_list)
    controller = TabController(form_ctrl, list_ctrl, record_type)
    return Tab(
        record_type=record_type,
        label=f"{record_type} Records",
        view=view,
        controller=controller,
    )
