import pytest

from record.service import create_record
from record.validator import RecordValidationError


def _client(**overrides) -> dict:
    base = {
        "ID": "1",
        "Name": "Alice",
        "Address Line 1": "1 Main St",
        "Address Line 2": "",
        "Address Line 3": "",
        "City": "NYC",
        "State": "NY",
        "Zip Code": "10001",
        "Country": "USA",
        "Phone Number": "555-0100",
    }
    base.update(overrides)
    return base


def _flight(**overrides) -> dict:
    base = {
        "Client_ID": "1",
        "Airline_ID": "2",
        "Date": "2026-06-01T09:00:00",
        "Start City": "NYC",
        "End City": "LAX",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Happy paths — each record type round-trips and produces typed IDs.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "record_type,payload,expected_subset",
    [
        pytest.param(
            "Client",
            _client(ID="42"),
            {"Type": "Client", "ID": 42},
            id="client-id-coerced-to-int",
        ),
        pytest.param(
            "Airline",
            {"ID": "7", "Company Name": "Acme"},
            {"Type": "Airline", "ID": 7, "Company Name": "Acme"},
            id="airline-canonical-record",
        ),
        pytest.param(
            "Flight",
            _flight(),
            {
                "Type": "Flight",
                "Client_ID": 1,
                "Airline_ID": 2,
                "Date": "2026-06-01T09:00:00",
            },
            id="flight-foreign-ids-coerced",
        ),
    ],
)
def test_create_record_happy_path(
    record_type: str, payload: dict, expected_subset: dict
) -> None:
    record = create_record(record_type, payload)
    for key, value in expected_subset.items():
        assert record[key] == value


# ---------------------------------------------------------------------------
# Unknown record type
# ---------------------------------------------------------------------------


def test_unknown_record_type_raises_validation_error() -> None:
    with pytest.raises(RecordValidationError, match="Unknown record type"):
        create_record("Hotel", {"ID": "1"})


# ---------------------------------------------------------------------------
# Validation order — the hotfix
#
# Empty required fields must still report "is required", not
# "must be a whole number", even after coercion runs first.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "record_type,payload_factory,field",
    [
        ("Client", lambda: _client(ID=""), "ID"),
        ("Client", lambda: _client(Name=""), "Name"),
        ("Client", lambda: _client(**{"Address Line 1": ""}), "Address Line 1"),
        ("Client", lambda: _client(Country=""), "Country"),
        ("Client", lambda: _client(Country="-- select --"), "Country"),
        ("Airline", lambda: {"ID": "", "Company Name": "Acme"}, "ID"),
        ("Airline", lambda: {"ID": "1", "Company Name": ""}, "Company Name"),
        ("Flight", lambda: _flight(Client_ID=""), "Client_ID"),
        ("Flight", lambda: _flight(Airline_ID=""), "Airline_ID"),
        ("Flight", lambda: _flight(Date=""), "Date"),
    ],
    ids=[
        "client-empty-id",
        "client-empty-name",
        "client-empty-address-1",
        "client-empty-country",
        "client-country-sentinel",
        "airline-empty-id",
        "airline-empty-company-name",
        "flight-empty-client-id",
        "flight-empty-airline-id",
        "flight-empty-date",
    ],
)
def test_empty_required_field_reports_required_message(
    record_type: str, payload_factory, field: str
) -> None:
    with pytest.raises(RecordValidationError, match=f"{field} is required"):
        create_record(record_type, payload_factory())


@pytest.mark.parametrize(
    "id_value",
    ["abc", "1.5", "1 2", "0x10", " "],
    ids=["letters", "float-string", "spaces-between", "hex", "single-space"],
)
def test_non_integer_id_reports_whole_number_message(id_value: str) -> None:
    with pytest.raises(RecordValidationError, match="ID must be a whole number"):
        create_record("Client", _client(ID=id_value))


# ---------------------------------------------------------------------------
# Integer coercion behaviour worth pinning down
# ---------------------------------------------------------------------------


def test_negative_integer_id_is_rejected() -> None:
    # Issue #18 requires invalid input to be rejected before saving.
    with pytest.raises(RecordValidationError, match="ID must be greater than zero"):
        create_record("Airline", {"ID": "-5", "Company Name": "X"})


def test_int_with_surrounding_whitespace_is_coerced() -> None:
    # int() tolerates leading/trailing whitespace; mirror that behaviour.
    record = create_record("Airline", {"ID": "  42 ", "Company Name": "X"})
    assert record["ID"] == 42


# ---------------------------------------------------------------------------
# Projection — unknown payload fields are dropped before persistence.
# ---------------------------------------------------------------------------


def test_unknown_payload_fields_are_dropped() -> None:
    record = create_record("Airline", {"ID": "1", "Company Name": "X", "Garbage": "z"})
    assert "Garbage" not in record


def test_only_type_and_allowed_fields_are_present() -> None:
    record = create_record("Airline", {"ID": "1", "Company Name": "X"})
    assert set(record.keys()) == {"Type", "ID", "Company Name"}


# ---------------------------------------------------------------------------
# Error-type contract — only RecordValidationError escapes the service.
# No bare ValueError / TypeError / KeyError should leak.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "record_type,payload",
    [
        pytest.param("UnknownType", {"ID": "1"}, id="unknown-type"),
        pytest.param("Client", _client(ID=""), id="client-empty-id"),
        pytest.param("Client", _client(ID="not-a-number"), id="client-bad-id-format"),
    ],
)
def test_all_failure_modes_raise_record_validation_error(
    record_type: str, payload: dict
) -> None:
    with pytest.raises(RecordValidationError):
        create_record(record_type, payload)
