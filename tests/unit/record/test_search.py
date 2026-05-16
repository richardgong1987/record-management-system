import pytest

from record.service import search_records


def _client(**overrides) -> dict:
    base = {
        "Type": "Client",
        "ID": 1,
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


def _airline(**overrides) -> dict:
    base = {"Type": "Airline", "ID": 2, "Company Name": "Skyways"}
    base.update(overrides)
    return base


def _flight(**overrides) -> dict:
    base = {
        "Type": "Flight",
        "Client_ID": 1,
        "Airline_ID": 2,
        "Date": "2026-06-01T09:00:00",
        "Start City": "NYC",
        "End City": "LAX",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Empty query returns every record of the requested type, nothing else.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("query", ["", "   ", "\t"])
def test_empty_query_returns_all_records_of_type(query: str) -> None:
    records = [
        _client(ID=1, Name="Alice"),
        _client(ID=2, Name="Bob"),
        _airline(),
        _flight(),
    ]

    result = search_records(records, "Client", query)

    assert result == [
        _client(ID=1, Name="Alice"),
        _client(ID=2, Name="Bob"),
    ]


def test_empty_query_on_record_type_with_no_rows_returns_empty_list() -> None:
    records = [_client(), _airline()]

    assert search_records(records, "Flight", "") == []


# ---------------------------------------------------------------------------
# Substring matching.
# ---------------------------------------------------------------------------


def test_substring_match_against_string_field() -> None:
    records = [
        _client(ID=1, Name="Alice"),
        _client(ID=2, Name="Bob"),
        _client(ID=3, Name="Alicia"),
    ]

    result = search_records(records, "Client", "ali")

    assert [r["Name"] for r in result] == ["Alice", "Alicia"]


def test_substring_match_is_case_insensitive() -> None:
    records = [_client(ID=1, Name="Alice"), _client(ID=2, Name="Bob")]

    assert search_records(records, "Client", "ALICE") == [_client(ID=1, Name="Alice")]


def test_substring_match_against_integer_field() -> None:
    # Records loaded after create_record have int IDs (coerced via int()), so
    # the helper must coerce both sides to string before comparing.
    records = [_client(ID=42, Name="Alice"), _client(ID=7, Name="Bob")]

    assert search_records(records, "Client", "42") == [_client(ID=42, Name="Alice")]


def test_match_searches_every_field_not_just_name() -> None:
    records = [
        _client(ID=1, Name="Alice", City="NYC"),
        _client(ID=2, Name="Bob", City="London"),
    ]

    assert search_records(records, "Client", "london") == [
        _client(ID=2, Name="Bob", City="London")
    ]


def test_no_match_returns_empty_list() -> None:
    records = [_client(Name="Alice"), _client(Name="Bob")]

    assert search_records(records, "Client", "zzz") == []


# ---------------------------------------------------------------------------
# Type isolation — substring matches in other types must not leak through.
# ---------------------------------------------------------------------------


def test_query_only_matches_records_of_the_requested_type() -> None:
    # "Alice" appears in a Client; the Airline tab must not surface it.
    records = [
        _client(Name="Alice"),
        _airline(**{"Company Name": "AliceAir"}),
    ]

    assert search_records(records, "Airline", "alice") == [
        _airline(**{"Company Name": "AliceAir"})
    ]
    assert search_records(records, "Client", "alice") == [_client(Name="Alice")]


def test_flight_search_matches_composite_key_field() -> None:
    records = [
        _flight(**{"Start City": "London", "End City": "Paris"}),
        _flight(**{"Start City": "NYC", "End City": "LAX"}),
    ]

    assert search_records(records, "Flight", "paris") == [
        _flight(**{"Start City": "London", "End City": "Paris"})
    ]


# ---------------------------------------------------------------------------
# Type discriminator is excluded — searching for "Client" must not return
# every client record on the Type field alone.
# ---------------------------------------------------------------------------


def test_type_field_is_not_searchable() -> None:
    records = [_client(Name="Alice"), _airline()]

    # If Type were searched, every Client would match "client".
    assert search_records(records, "Client", "client") == []


# ---------------------------------------------------------------------------
# Immutability — the helper must not mutate or alias the input list/records.
# ---------------------------------------------------------------------------


def test_does_not_mutate_input_records_list() -> None:
    records = [_client(Name="Alice"), _client(Name="Bob")]
    snapshot = [dict(r) for r in records]

    search_records(records, "Client", "ali")

    assert records == snapshot


def test_returns_new_list_object() -> None:
    records = [_client(Name="Alice")]

    result = search_records(records, "Client", "")

    assert result is not records
