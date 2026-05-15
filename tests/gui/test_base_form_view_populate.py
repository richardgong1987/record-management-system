import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_populate_fills_line_edits_from_record_dict(qapp) -> None:
    from gui.client.view import ClientFormView

    view = ClientFormView()
    view.populate(
        {
            "ID": 42,
            "Name": "Alice",
            "Address Line 1": "1 Main St",
            "City": "NYC",
            "State": "NY",
            "Zip Code": "10001",
            "Country": "USA",
            "Phone Number": "555-0100",
        }
    )

    # Numbers from the data layer are stringified back into the widget.
    assert view.form_inputs["ID"].text() == "42"
    assert view.form_inputs["Name"].text() == "Alice"
    assert view.form_inputs["Address Line 1"].text() == "1 Main St"
    assert view.form_inputs["Country"].currentText() == "USA"


def test_populate_resets_combo_to_placeholder_when_value_unknown(qapp) -> None:
    from gui.client.view import ClientFormView

    view = ClientFormView()
    view.populate({"Country": "Atlantis"})  # not in the COUNTRIES list

    # Index 0 is the "-- select --" placeholder by convention.
    assert view.form_inputs["Country"].currentIndex() == 0


def test_populate_round_trips_through_read_payload(qapp) -> None:
    from gui.airline.view import AirlineFormView

    view = AirlineFormView()
    view.populate({"ID": 7, "Company Name": "Acme"})

    assert view.read_payload() == {"ID": "7", "Company Name": "Acme"}


def test_populate_handles_missing_keys_as_empty(qapp) -> None:
    from gui.flight.view import FlightFormView

    view = FlightFormView()
    # Only set two of the five expected fields.
    view.populate({"Start City": "NYC", "End City": "LAX"})

    assert view.form_inputs["Start City"].text() == "NYC"
    assert view.form_inputs["End City"].text() == "LAX"
    assert view.form_inputs["Date"].text() == ""
    assert view.form_inputs["Client_ID"].text() == ""


def test_populate_then_clear_empties_every_field(qapp) -> None:
    from gui.client.view import ClientFormView

    view = ClientFormView()
    view.populate(
        {"ID": 1, "Name": "Alice", "Country": "UK", "Phone Number": "555-0100"}
    )
    view.clear()

    assert view.form_inputs["ID"].text() == ""
    assert view.form_inputs["Name"].text() == ""
    assert view.form_inputs["Country"].currentIndex() == 0