"""Per-record-type tab construction recipe.

Single source of truth for which form view / form controller / table
columns each record type uses. Pulled out of ``main_window`` so adding
a new record type means editing one short module, and so the main
window stays under the 300-line cap.
"""

from gui.airline.controller import AirlineFormController
from gui.airline.types import AIRLINE_TEXT_FIELDS
from gui.airline.view import AirlineFormView
from gui.client.controller import ClientFormController
from gui.client.types import CLIENT_TEXT_FIELDS
from gui.client.view import ClientFormView
from gui.flight.controller import FlightFormController
from gui.flight.types import FLIGHT_TEXT_FIELDS
from gui.flight.view import FlightFormView

# Per record type: (form view class, form controller class, table columns).
# Add a new key to introduce a new tab — the rest is wired automatically.
RECORD_TYPES = {
    "Client": (ClientFormView, ClientFormController, CLIENT_TEXT_FIELDS),
    "Airline": (AirlineFormView, AirlineFormController, AIRLINE_TEXT_FIELDS),
    "Flight": (FlightFormView, FlightFormController, FLIGHT_TEXT_FIELDS),
}
