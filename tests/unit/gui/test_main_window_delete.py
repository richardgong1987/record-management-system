import os

# Offscreen must be set before QApplication is imported.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication


def _client_payload(name: str = "Alice") -> dict:
    # ID intentionally omitted — Client IDs are auto-assigned.
    return {
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


def _airline_payload(company: str = "Acme") -> dict:
    # ID intentionally omitted — Airline IDs are auto-assigned.
    return {"Company Name": company}


def _flight_payload() -> dict:
    return {
        "Client_ID": "1",
        "Airline_ID": "2",
        "Date": "2026-06-01T09:00:00",
        "Start City": "NYC",
        "End City": "LAX",
    }


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def main_window(qapp, monkeypatch, tmp_path):
    from gui import main_window as mw

    monkeypatch.setattr(mw, "DATA_FILE_PATH", tmp_path / "record.jsonl")
    window = mw.MainWindow()
    # Default the confirmation dialog to Yes so tests don't pop a real
    # QMessageBox. Individual tests override this when they want to
    # simulate the user declining.
    monkeypatch.setattr(mw, "confirm", lambda *_args, **_kwargs: True)
    return window


def _seed_client(window, **overrides) -> dict:
    window._on_create("Client", _client_payload(**overrides))
    return window._records[-1]


# ---------------------------------------------------------------------------
# Guard rails: clicking Delete without a real selection must not touch
# anything. Two flavours of "no selection": never selected, or selected a
# dict that's no longer in _records (identity check fails).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "stale_selection",
    [
        pytest.param(False, id="no-selection-ever"),
        pytest.param(True, id="stale-selection"),
    ],
)
def test_delete_without_valid_selection_is_a_no_op(
    main_window, stale_selection: bool
) -> None:
    _seed_client(main_window)
    if stale_selection:
        # A dict not in _records — identity check should reject it.
        main_window._selected_record_by_type["Client"] = {
            "Type": "Client",
            "stale": True,
        }
    before = list(main_window._records)

    main_window._on_delete("Client", {})

    assert main_window._records == before


def test_delete_without_selection_reports_required_message(main_window) -> None:
    _seed_client(main_window)
    main_window._on_delete("Client", {})
    assert "Select a record to delete first." in main_window.status._status_lbl.text()


# ---------------------------------------------------------------------------
# User declines confirmation — nothing happens.
# ---------------------------------------------------------------------------


def test_declined_confirmation_leaves_records_untouched(
    qapp, monkeypatch, tmp_path
) -> None:
    # Re-build the window without the fixture's auto-yes so we can wire a No.
    from gui import main_window as mw

    monkeypatch.setattr(mw, "DATA_FILE_PATH", tmp_path / "record.jsonl")
    window = mw.MainWindow()
    monkeypatch.setattr(mw, "confirm", lambda *_args, **_kwargs: False)

    window._on_create("Client", _client_payload())
    window._on_record_selected("Client", 0)
    before = list(window._records)

    window._on_delete("Client", {})

    assert window._records == before
    assert "Delete cancelled." in window.status._status_lbl.text()


# ---------------------------------------------------------------------------
# Happy path — record is removed from memory and from disk.
# ---------------------------------------------------------------------------


def test_confirmed_delete_removes_selected_record(main_window) -> None:
    _seed_client(main_window, name="Alice")
    _seed_client(main_window, name="Bob")
    main_window._on_record_selected("Client", 0)

    main_window._on_delete("Client", {})

    assert len(main_window._records) == 1
    assert main_window._records[0]["Name"] == "Bob"


def test_confirmed_delete_persists_to_disk(main_window) -> None:
    from gui import main_window as mw

    _seed_client(main_window, name="Alice")
    _seed_client(main_window, name="Bob")
    main_window._on_record_selected("Client", 0)
    main_window._on_delete("Client", {})

    import jsonlines

    with jsonlines.open(mw.DATA_FILE_PATH) as reader:
        on_disk = list(reader)
    assert on_disk == main_window._records
    assert all(r["Name"] != "Alice" for r in on_disk)


@pytest.mark.parametrize(
    "create_calls,select_args,expected_remaining",
    [
        pytest.param(
            [
                ("Airline", _airline_payload()),
                ("Airline", _airline_payload(company="Beta")),
            ],
            ("Airline", 1),
            [{"Type": "Airline", "ID": 1, "Company Name": "Acme"}],
            id="airline",
        ),
        pytest.param(
            [("Flight", _flight_payload())],
            ("Flight", 0),
            [],
            id="flight-no-own-id",
        ),
    ],
)
def test_delete_works_for_record_type(
    main_window,
    create_calls: list,
    select_args: tuple,
    expected_remaining: list,
) -> None:
    for record_type, payload in create_calls:
        main_window._on_create(record_type, payload)
    main_window._on_record_selected(*select_args)

    main_window._on_delete(select_args[0], {})

    assert main_window._records == expected_remaining


def test_delete_last_record_writes_empty_file(main_window) -> None:
    from gui import main_window as mw

    _seed_client(main_window)
    main_window._on_record_selected("Client", 0)
    main_window._on_delete("Client", {})

    assert main_window._records == []
    # File should exist and be empty — load_records should round-trip to [].
    assert mw.DATA_FILE_PATH.exists()
    assert mw.DATA_FILE_PATH.read_text() == ""


# ---------------------------------------------------------------------------
# Post-delete state — form cleared, selection forgotten.
# ---------------------------------------------------------------------------


def test_deleting_the_only_record_clears_the_form(main_window) -> None:
    _seed_client(main_window, name="Alice")
    main_window._on_record_selected("Client", 0)
    form = main_window._tabs_by_type["Client"].view.form
    assert form.form_inputs["Name"].text() == "Alice"  # populated before delete

    main_window._on_delete("Client", {})

    assert form.form_inputs["Name"].text() == ""
    assert form.form_inputs["ID"].text() == ""


def test_deleting_the_only_record_drops_the_selection_to_none(main_window) -> None:
    _seed_client(main_window)
    main_window._on_record_selected("Client", 0)
    assert main_window._selected_record_by_type["Client"] is main_window._records[0]

    main_window._on_delete("Client", {})

    assert main_window._selected_record_by_type["Client"] is None


def test_consecutive_delete_clicks_keep_removing_rows(main_window) -> None:
    """The user-reported follow-up bug: after deleting one record, clicking
    Delete again must remove the next record without forcing another row
    click. Selection clamps to the same table-row position so 'Delete'
    becomes a 'remove next' button when held over the same logical slot."""
    _seed_client(main_window, name="Alice")
    _seed_client(main_window, name="Bob")
    _seed_client(main_window, name="Carol")

    main_window._on_record_selected("Client", 0)
    main_window._on_delete("Client", {})  # removes Alice
    main_window._on_delete("Client", {})  # must remove Bob without re-clicking
    main_window._on_delete("Client", {})  # must remove Carol

    assert main_window._records == []
    assert main_window._selected_record_by_type["Client"] is None


def test_delete_repopulates_form_with_the_record_now_at_that_position(
    main_window,
) -> None:
    _seed_client(main_window, name="Alice")
    _seed_client(main_window, name="Bob")
    main_window._on_record_selected("Client", 0)

    main_window._on_delete("Client", {})

    form = main_window._tabs_by_type["Client"].view.form
    assert form.form_inputs["Name"].text() == "Bob"
    # Selection now points to the surviving record at the same table position.
    assert main_window._selected_record_by_type["Client"] is main_window._records[0]


def test_deleting_the_last_row_clamps_selection_to_the_new_last(main_window) -> None:
    _seed_client(main_window, name="Alice")
    _seed_client(main_window, name="Bob")
    main_window._on_record_selected("Client", 1)  # Bob, the last row

    main_window._on_delete("Client", {})

    form = main_window._tabs_by_type["Client"].view.form
    assert form.form_inputs["Name"].text() == "Alice"
    assert main_window._selected_record_by_type["Client"] is main_window._records[0]


def test_delete_clamping_stays_within_the_same_record_type(main_window) -> None:
    """Selection lives in _records (mixed types), but the page-row position
    we clamp to is within the type-filtered list — so deleting a Client
    must never accidentally select an Airline at the same absolute index."""
    main_window._on_create("Airline", {"ID": "1", "Company Name": "Acme"})
    _seed_client(main_window, name="Alice")
    _seed_client(main_window, name="Bob")
    main_window._on_record_selected("Client", 0)  # Alice (abs idx 1)

    main_window._on_delete("Client", {})

    # The new selection must point to Bob, not the Airline at abs idx 0.
    selected = main_window._selected_record_by_type["Client"]
    assert selected["Type"] == "Client"
    assert selected["Name"] == "Bob"


# ---------------------------------------------------------------------------
# Persistence failure — never let in-memory state move ahead of disk.
#
# OSError and PermissionError (an OSError subclass) must both be caught
# without propagating; selection must NOT be cleared on failure (the user
# may want to retry).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "exc",
    [
        pytest.param(OSError("Disk full"), id="disk-full-oserror"),
        pytest.param(PermissionError("read-only"), id="permission-error"),
    ],
)
def test_save_failure_during_delete_leaves_records_untouched(
    main_window, monkeypatch, exc: OSError
) -> None:
    from gui import main_window as mw

    _seed_client(main_window)
    _seed_client(main_window)
    main_window._on_record_selected("Client", 0)
    before = list(main_window._records)

    def raise_exc(*_args, **_kwargs):
        raise exc

    monkeypatch.setattr(mw, "save_records", raise_exc)
    main_window._on_delete("Client", {})

    assert main_window._records == before
    assert main_window._selected_record_by_type["Client"] is main_window._records[0]


# ---------------------------------------------------------------------------
# Codex P1 regression: identity-based selection.
#
# Two Flight records with identical field values are allowed (no own-ID
# uniqueness rule). The previous implementation resolved the selected
# absolute index via self._records.index(record), which used dict equality
# and returned the FIRST match — so clicking the second duplicate row and
# clicking Delete would actually remove the first. Identity-based storage
# fixes it: the dict reference of the clicked row is unique even when its
# contents aren't.
# ---------------------------------------------------------------------------


def test_selecting_one_of_two_identical_flights_deletes_the_correct_row(
    main_window,
) -> None:
    main_window._on_create("Flight", _flight_payload())
    main_window._on_create("Flight", _flight_payload())  # identical values
    assert len(main_window._records) == 2

    first, second = main_window._records[0], main_window._records[1]

    # Click the SECOND row in the Flight table.
    main_window._on_record_selected("Flight", 1)
    assert main_window._selected_record_by_type["Flight"] is second

    main_window._on_delete("Flight", {})

    assert len(main_window._records) == 1
    # The survivor must be the FIRST flight (by identity), not the second.
    assert main_window._records[0] is first
