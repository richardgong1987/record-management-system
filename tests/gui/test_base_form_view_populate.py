import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def _client_view():
    from gui.client.view import ClientFormView

    return ClientFormView()


def _airline_view():
    from gui.airline.view import AirlineFormView

    return AirlineFormView()


def _flight_view():
    from gui.flight.view import FlightFormView

    return FlightFormView()


# ---------------------------------------------------------------------------
# populate(record) writes values into matching widgets, stringifies non-str
# values from the data layer, and leaves widgets whose key is missing from
# the record empty.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "view_factory,record,expected_line_edit_text,expected_combo_text",
    [
        pytest.param(
            _client_view,
            {
                "ID": 42,
                "Name": "Alice",
                "Address Line 1": "1 Main St",
                "City": "NYC",
                "State": "NY",
                "Zip Code": "10001",
                "Country": "USA",
                "Phone Number": "555-0100",
            },
            # Numbers from the data layer are stringified back into the widget.
            {"ID": "42", "Name": "Alice", "Address Line 1": "1 Main St"},
            {"Country": "USA"},
            id="client-full-record",
        ),
        pytest.param(
            _flight_view,
            {"Start City": "NYC", "End City": "LAX"},
            # Only two of the five expected fields are set; the rest stay empty.
            {
                "Start City": "NYC",
                "End City": "LAX",
                "Date": "",
                "Client_ID": "",
            },
            {},
            id="flight-partial-leaves-rest-empty",
        ),
    ],
)
def test_populate_writes_record_values_into_widgets(
    qapp,
    view_factory,
    record: dict,
    expected_line_edit_text: dict,
    expected_combo_text: dict,
) -> None:
    view = view_factory()
    view.populate(record)

    for field, text in expected_line_edit_text.items():
        assert view.form_inputs[field].text() == text
    for field, text in expected_combo_text.items():
        assert view.form_inputs[field].currentText() == text


def test_populate_resets_combo_to_placeholder_when_value_unknown(qapp) -> None:
    view = _client_view()
    view.populate({"Country": "Atlantis"})  # not in the COUNTRIES list

    # Index 0 is the "-- select --" placeholder by convention.
    assert view.form_inputs["Country"].currentIndex() == 0


def test_populate_round_trips_through_read_payload(qapp) -> None:
    view = _airline_view()
    view.populate({"ID": 7, "Company Name": "Acme"})

    assert view.read_payload() == {"ID": "7", "Company Name": "Acme"}


# ---------------------------------------------------------------------------
# clear() empties every field — both line edits and any combo placeholders.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "view_factory,populate_record,empty_line_edits,empty_combo_indices",
    [
        pytest.param(
            _client_view,
            {"ID": 1, "Name": "Alice", "Country": "UK", "Phone Number": "555-0100"},
            ["ID", "Name", "Phone Number"],
            {"Country": 0},
            id="client",
        ),
        pytest.param(
            _airline_view,
            {"ID": 7, "Company Name": "Acme"},
            ["ID", "Company Name"],
            {},
            id="airline",
        ),
        pytest.param(
            _flight_view,
            {
                "Client_ID": "1",
                "Airline_ID": "2",
                "Date": "2026-06-01T09:00:00",
                "Start City": "NYC",
                "End City": "LAX",
            },
            ["Client_ID", "Airline_ID", "Date", "Start City", "End City"],
            {},
            id="flight",
        ),
    ],
)
def test_populate_then_clear_empties_every_field(
    qapp,
    view_factory,
    populate_record: dict,
    empty_line_edits: list,
    empty_combo_indices: dict,
) -> None:
    view = view_factory()
    view.populate(populate_record)
    view.clear()

    for field in empty_line_edits:
        assert view.form_inputs[field].text() == ""
    for field, expected_index in empty_combo_indices.items():
        assert view.form_inputs[field].currentIndex() == expected_index
