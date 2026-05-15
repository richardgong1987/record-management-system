import pytest

from record.validator import (
    RecordValidationError,
    check_flight_date,
    check_positive_integers,
)


# ---------------------------------------------------------------------------
# check_positive_integers
# ---------------------------------------------------------------------------


def test_check_positive_integers_rejects_zero() -> None:
    with pytest.raises(RecordValidationError, match="ID must be greater than zero"):
        check_positive_integers({"Type": "Client", "ID": 0})


def test_check_positive_integers_rejects_negative() -> None:
    with pytest.raises(RecordValidationError, match="ID must be greater than zero"):
        check_positive_integers({"Type": "Client", "ID": -1})


def test_check_positive_integers_accepts_positive() -> None:
    check_positive_integers({"Type": "Client", "ID": 1})


def test_check_positive_integers_ignores_missing_integer_fields() -> None:
    check_positive_integers({"Type": "Client", "Name": "Arjun"})


def test_check_positive_integers_accepts_airline_id() -> None:
    check_positive_integers({"Type": "Airline", "ID": 1})


def test_check_positive_integers_checks_flight_ids() -> None:
    with pytest.raises(
        RecordValidationError,
        match="Airline_ID must be greater than zero",
    ):
        check_positive_integers({"Type": "Flight", "Client_ID": 1, "Airline_ID": 0})


# ---------------------------------------------------------------------------
# check_flight_date
# ---------------------------------------------------------------------------


def test_check_flight_date_accepts_valid_datetime() -> None:
    check_flight_date({"Type": "Flight", "Date": "2026-05-13T14:30:00"})


def test_check_flight_date_accepts_valid_date_only() -> None:
    check_flight_date({"Type": "Flight", "Date": "2026-05-13"})


def test_check_flight_date_rejects_malformed_string() -> None:
    with pytest.raises(RecordValidationError, match="Date must use ISO format"):
        check_flight_date({"Type": "Flight", "Date": "not-a-date"})


def test_check_flight_date_rejects_empty_string() -> None:
    with pytest.raises(RecordValidationError, match="Date must use ISO format"):
        check_flight_date({"Type": "Flight", "Date": ""})


def test_check_flight_date_rejects_none() -> None:
    # Direct callers may pass None instead of an empty string; the validator
    # must surface the same ISO-format error rather than a TypeError.
    with pytest.raises(RecordValidationError, match="Date must use ISO format"):
        check_flight_date({"Type": "Flight", "Date": None})


def test_check_flight_date_rejects_missing_date_key() -> None:
    # Same contract when the Date key is absent entirely.
    with pytest.raises(RecordValidationError, match="Date must use ISO format"):
        check_flight_date({"Type": "Flight"})


def test_check_flight_date_ignores_non_flight_records() -> None:
    check_flight_date({"Type": "Client", "Date": "not-a-date"})
