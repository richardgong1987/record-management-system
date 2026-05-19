"""Create / update / delete round-trip through service + repository.

No GUI, no mocks — a real JSONL file in ``tmp_path`` is written by
``save_records`` and read back by ``load_records`` between every step,
so type coercion or serialisation drift between the two layers shows
up immediately.

See docs/design/integration-tests.md for the test taxonomy.
"""

import pytest

from record.repository import load_records, save_records
from record.service import create_record


def _client_payload(id_value: str = "1", name: str = "Alice") -> dict:
    return {
        "ID": id_value,
        "Name": name,
        "Address Line 1": "1 Main St",
        "Address Line 2": "",
        "Address Line 3": "",
        "City": "NYC",
        "State": "NY",
        "Zip Code": "10001",
        "Country": "USA",
        "Phone Number": "555-0100",
    }


def _airline_payload(id_value: str = "1", company: str = "Acme") -> dict:
    return {"ID": id_value, "Company Name": company}


def _flight_payload(
    client_id: str = "1",
    airline_id: str = "1",
    date: str = "2026-06-01T09:00:00",
) -> dict:
    return {
        "Client_ID": client_id,
        "Airline_ID": airline_id,
        "Date": date,
        "Start City": "London",
        "End City": "Tokyo",
    }


@pytest.fixture
def store_path(tmp_path):
    # Each test gets its own JSONL file. Returning the path (not a writer)
    # keeps the fixture trivial — tests still call save_records/load_records
    # directly so the seam stays visible in the test body.
    return tmp_path / "records.jsonl"


# ---------------------------------------------------------------------------
# Create — every record type round-trips through validation, save, and reload.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "record_type,payload",
    [
        pytest.param("Client", _client_payload(), id="client"),
        pytest.param("Airline", _airline_payload(), id="airline"),
        pytest.param("Flight", _flight_payload(), id="flight"),
    ],
)
def test_create_then_reload_persists_record(
    store_path, record_type: str, payload: dict
) -> None:
    record = create_record(record_type, payload)

    save_records(store_path, [record])

    assert load_records(store_path) == [record]


def test_create_preserves_other_records_on_reload(store_path) -> None:
    # Mixed-type store — making sure the JSONL writer doesn't reorder or
    # drop records when types are interleaved.
    records = [
        create_record("Client", _client_payload(id_value="1", name="Alice")),
        create_record("Airline", _airline_payload(id_value="1", company="Acme")),
        create_record("Flight", _flight_payload()),
    ]

    save_records(store_path, records)

    assert load_records(store_path) == records


# ---------------------------------------------------------------------------
# Update — replace one record in the list, persist, reload, verify.
# ---------------------------------------------------------------------------


def test_update_replaces_record_in_place(store_path) -> None:
    original = create_record("Client", _client_payload(id_value="1", name="Alice"))
    other = create_record("Client", _client_payload(id_value="2", name="Bob"))
    save_records(store_path, [original, other])

    on_disk = load_records(store_path)
    updated = create_record("Client", _client_payload(id_value="1", name="Alicia"))
    new_list = [updated if r["ID"] == 1 else r for r in on_disk]
    save_records(store_path, new_list)

    reloaded = load_records(store_path)
    assert [r["Name"] for r in reloaded] == ["Alicia", "Bob"]
    # Position is preserved — the table renders in stored order, so an
    # update must not reorder neighbours.
    assert reloaded[0]["ID"] == 1
    assert reloaded[1]["ID"] == 2


def test_update_unrelated_record_types_untouched(store_path) -> None:
    client = create_record("Client", _client_payload())
    airline = create_record("Airline", _airline_payload())
    save_records(store_path, [client, airline])

    on_disk = load_records(store_path)
    updated_airline = create_record(
        "Airline", _airline_payload(id_value="1", company="British Airways")
    )
    new_list = [updated_airline if r["Type"] == "Airline" else r for r in on_disk]
    save_records(store_path, new_list)

    reloaded = load_records(store_path)
    # Client row reloads byte-for-byte; the airline rewrite did not disturb it.
    assert next(r for r in reloaded if r["Type"] == "Client") == client
    assert next(r for r in reloaded if r["Type"] == "Airline")["Company Name"] == (
        "British Airways"
    )


# ---------------------------------------------------------------------------
# Delete — drop one record from the list, persist, reload, verify.
# ---------------------------------------------------------------------------


def test_delete_removes_only_target_record(store_path) -> None:
    keep = create_record("Client", _client_payload(id_value="1", name="Keep"))
    drop = create_record("Client", _client_payload(id_value="2", name="Drop"))
    save_records(store_path, [keep, drop])

    on_disk = load_records(store_path)
    new_list = [r for r in on_disk if r["ID"] != 2]
    save_records(store_path, new_list)

    assert load_records(store_path) == [keep]


def test_delete_last_record_writes_empty_jsonl(store_path) -> None:
    only = create_record("Client", _client_payload())
    save_records(store_path, [only])

    save_records(store_path, [])

    # An empty JSONL is a valid store — repository must read it back as [],
    # not raise. This is the seam most likely to bite us on a fresh install
    # or after a clear-all of the last record.
    assert load_records(store_path) == []
