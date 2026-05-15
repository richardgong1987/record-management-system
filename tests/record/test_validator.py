import pytest

from record.validator import (
    RecordValidationError,
    check_flight_date,
    check_positive_integers,
)


# ---------------------------------------------------------------------------
# check_positive_integers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "record,expected_field",
    [
        pytest.param({"Type": "Client", "ID": 0}, "ID", id="client-id-zero"),
        pytest.param({"Type": "Client", "ID": -1}, "ID", id="client-id-negative"),
        pytest.param(
            {"Type": "Flight", "Client_ID": 1, "Airline_ID": 0},
            "Airline_ID",
            id="flight-airline-id-zero",
        ),
    ],
)
def test_check_positive_integers_rejects_non_positive(
    record: dict, expected_field: str
) -> None:
    with pytest.raises(
        RecordValidationError,
        match=f"{expected_field} must be greater than zero",
    ):
        check_positive_integers(record)


@pytest.mark.parametrize(
    "record",
    [
        pytest.param({"Type": "Client", "ID": 1}, id="client-id-one"),
        pytest.param({"Type": "Airline", "ID": 1}, id="airline-id-one"),
        pytest.param(
            {"Type": "Client", "Name": "Arjun"}, id="missing-integer-fields-ignored"
        ),
    ],
)
def test_check_positive_integers_accepts_valid_records(record: dict) -> None:
    check_positive_integers(record)


# ---------------------------------------------------------------------------
# check_flight_date
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "record",
    [
        pytest.param(
            {"Type": "Flight", "Date": "2026-05-13T14:30:00"}, id="iso-datetime"
        ),
        pytest.param({"Type": "Flight", "Date": "2026-05-13"}, id="iso-date-only"),
        pytest.param(
            {"Type": "Client", "Date": "not-a-date"}, id="non-flight-record-ignored"
        ),
    ],
)
def test_check_flight_date_accepts(record: dict) -> None:
    check_flight_date(record)


@pytest.mark.parametrize(
    "record",
    [
        pytest.param(
            {"Type": "Flight", "Date": "not-a-date"}, id="malformed-string"
        ),
        pytest.param({"Type": "Flight", "Date": ""}, id="empty-string"),
        # Direct callers may pass None instead of empty string; the validator
        # must surface the same ISO-format error rather than a TypeError.
        pytest.param({"Type": "Flight", "Date": None}, id="none-value"),
        # Same contract when the Date key is absent entirely.
        pytest.param({"Type": "Flight"}, id="missing-date-key"),
    ],
)
def test_check_flight_date_rejects(record: dict) -> None:
    with pytest.raises(RecordValidationError, match="Date must use ISO format"):
        check_flight_date(record)
