"""Search + pagination composition over a real JSONL round-trip.

Seeds a JSONL file via the same service + repository the GUI uses,
reloads it, then asks ``search_records`` + ``paginate`` for a page
of results. The point is to pin the clamp behaviour at the seam:
when a search narrows the row set, a stale page index must clamp
back to a valid page.

See docs/design/integration-tests.md.
"""

import pytest

from record.repository import load_records, save_records
from record.service import create_record, search_records
from shared.utils.pagination import DEFAULT_PAGE_SIZE, paginate


def _client(id_value: int, name: str) -> dict:
    return create_record(
        "Client",
        {
            "ID": str(id_value),
            "Name": name,
            "Address Line 1": f"{id_value} Main St",
            "Address Line 2": "",
            "Address Line 3": "",
            "City": "NYC" if id_value % 2 else "London",
            "State": "NY",
            "Zip Code": "10001",
            "Country": "USA",
            "Phone Number": "555-0100",
        },
    )


@pytest.fixture
def seeded_store(tmp_path):
    # Seed 30 Client records (two full pages at DEFAULT_PAGE_SIZE=15) plus
    # an Airline so we can also confirm search_records filters by Type.
    path = tmp_path / "records.jsonl"
    clients = [_client(i, f"Person{i:02d}") for i in range(1, 31)]
    airline = create_record("Airline", {"ID": "1", "Company Name": "Acme"})
    save_records(path, clients + [airline])
    return path


def test_show_all_returns_every_record_of_the_requested_type(seeded_store) -> None:
    records = load_records(seeded_store)

    clients = search_records(records, "Client", "")

    assert len(clients) == 30
    assert all(r["Type"] == "Client" for r in clients)


def test_pagination_splits_show_all_into_two_pages(seeded_store) -> None:
    records = load_records(seeded_store)
    clients = search_records(records, "Client", "")

    page1 = paginate(clients, current_page=1)
    page2 = paginate(clients, current_page=2)

    assert page1.current_page == 1
    assert page1.total_pages == 2
    assert len(page1.rows) == DEFAULT_PAGE_SIZE
    assert page2.current_page == 2
    assert len(page2.rows) == 30 - DEFAULT_PAGE_SIZE


def test_search_narrows_result_set(seeded_store) -> None:
    records = load_records(seeded_store)

    # Person07 matches exactly one record; "NYC" matches every odd-ID client.
    one_match = search_records(records, "Client", "Person07")
    city_matches = search_records(records, "Client", "NYC")

    assert [r["Name"] for r in one_match] == ["Person07"]
    assert len(city_matches) == 15  # odd IDs 1..29


def test_page_clamps_when_search_shrinks_result_below_current_page(
    seeded_store,
) -> None:
    # Reproduces the GUI sequence: user is on page 2, types a query that
    # leaves one match. paginate must clamp the requested page 2 back to 1.
    records = load_records(seeded_store)
    narrowed = search_records(records, "Client", "Person07")

    page = paginate(narrowed, current_page=2)

    assert page.current_page == 1
    assert page.total_pages == 1
    assert [r["Name"] for r in page.rows] == ["Person07"]


def test_empty_search_result_returns_clamped_empty_page(seeded_store) -> None:
    records = load_records(seeded_store)
    none_match = search_records(records, "Client", "no-such-name")

    page = paginate(none_match, current_page=5)

    assert page.rows == []
    assert page.total_pages == 1
    assert page.current_page == 1


def test_search_is_type_scoped(seeded_store) -> None:
    # "Acme" is the only Airline in the store. Searching the Client tab
    # for "Acme" must return zero rows — search must never leak across
    # record types, even when the query matches.
    records = load_records(seeded_store)

    client_hits = search_records(records, "Client", "Acme")
    airline_hits = search_records(records, "Airline", "Acme")

    assert client_hits == []
    assert [r["Company Name"] for r in airline_hits] == ["Acme"]
