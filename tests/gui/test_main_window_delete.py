import os

# Offscreen must be set before QApplication is imported.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication


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
# Guard rail: clicking Delete without a selection must not touch anything.
# ---------------------------------------------------------------------------


def test_delete_without_selection_reports_required_message(main_window) -> None:
    _seed_client(main_window, id_value="1")
    before = list(main_window._records)

    main_window._on_delete("Client", {})

    assert main_window._records == before
    assert "Select a record to delete first." in main_window.status._status_lbl.text()


def test_delete_with_stale_selection_index_is_treated_as_no_selection(
    main_window,
) -> None:
    _seed_client(main_window, id_value="1")
    main_window._selected_index_by_type["Client"] = 99
    before = list(main_window._records)

    main_window._on_delete("Client", {})

    assert main_window._records == before


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

    window._on_create("Client", _client_payload(id_value="1"))
    window._on_record_selected("Client", 0)
    before = list(window._records)

    window._on_delete("Client", {})

    assert window._records == before
    assert "Delete cancelled." in window.status._status_lbl.text()


# ---------------------------------------------------------------------------
# Happy path — record is removed from memory and from disk.
# ---------------------------------------------------------------------------


def test_confirmed_delete_removes_selected_record(main_window) -> None:
    _seed_client(main_window, id_value="1", name="Alice")
    _seed_client(main_window, id_value="2", name="Bob")
    main_window._on_record_selected("Client", 0)

    main_window._on_delete("Client", {})

    assert len(main_window._records) == 1
    assert main_window._records[0]["Name"] == "Bob"


def test_confirmed_delete_persists_to_disk(main_window) -> None:
    from gui import main_window as mw

    _seed_client(main_window, id_value="1", name="Alice")
    _seed_client(main_window, id_value="2", name="Bob")
    main_window._on_record_selected("Client", 0)
    main_window._on_delete("Client", {})

    import jsonlines

    with jsonlines.open(mw.DATA_FILE_PATH) as reader:
        on_disk = list(reader)
    assert on_disk == main_window._records
    assert all(r["Name"] != "Alice" for r in on_disk)


def test_delete_works_for_airline_records(main_window) -> None:
    main_window._on_create("Airline", _airline_payload(id_value="1"))
    main_window._on_create("Airline", _airline_payload(id_value="2", company="Beta"))
    main_window._on_record_selected("Airline", 1)

    main_window._on_delete("Airline", {})

    assert len(main_window._records) == 1
    assert main_window._records[0]["ID"] == 1


def test_delete_works_for_flight_records_which_have_no_own_id(main_window) -> None:
    main_window._on_create("Flight", _flight_payload())
    main_window._on_record_selected("Flight", 0)

    main_window._on_delete("Flight", {})

    assert main_window._records == []


def test_delete_last_record_writes_empty_file(main_window) -> None:
    from gui import main_window as mw

    _seed_client(main_window, id_value="1")
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
    _seed_client(main_window, id_value="1", name="Alice")
    main_window._on_record_selected("Client", 0)
    form = main_window._tabs_by_type["Client"].view.form
    assert form.form_inputs["Name"].text() == "Alice"  # populated before delete

    main_window._on_delete("Client", {})

    assert form.form_inputs["Name"].text() == ""
    assert form.form_inputs["ID"].text() == ""


def test_deleting_the_only_record_drops_the_selection_to_none(main_window) -> None:
    _seed_client(main_window, id_value="1")
    main_window._on_record_selected("Client", 0)
    assert main_window._selected_index_by_type["Client"] == 0

    main_window._on_delete("Client", {})

    assert main_window._selected_index_by_type["Client"] is None


def test_consecutive_delete_clicks_keep_removing_rows(main_window) -> None:
    """The user-reported follow-up bug: after deleting one record, clicking
    Delete again must remove the next record without forcing another row
    click. Selection clamps to the same table-row position so 'Delete'
    becomes a 'remove next' button when held over the same logical slot."""
    _seed_client(main_window, id_value="1", name="Alice")
    _seed_client(main_window, id_value="2", name="Bob")
    _seed_client(main_window, id_value="3", name="Carol")

    main_window._on_record_selected("Client", 0)
    main_window._on_delete("Client", {})  # removes Alice
    main_window._on_delete("Client", {})  # must remove Bob without re-clicking
    main_window._on_delete("Client", {})  # must remove Carol

    assert main_window._records == []
    assert main_window._selected_index_by_type["Client"] is None


def test_delete_repopulates_form_with_the_record_now_at_that_position(
    main_window,
) -> None:
    _seed_client(main_window, id_value="1", name="Alice")
    _seed_client(main_window, id_value="2", name="Bob")
    main_window._on_record_selected("Client", 0)

    main_window._on_delete("Client", {})

    form = main_window._tabs_by_type["Client"].view.form
    assert form.form_inputs["Name"].text() == "Bob"
    assert main_window._selected_index_by_type["Client"] == 0


def test_deleting_the_last_row_clamps_selection_to_the_new_last(main_window) -> None:
    _seed_client(main_window, id_value="1", name="Alice")
    _seed_client(main_window, id_value="2", name="Bob")
    main_window._on_record_selected("Client", 1)  # Bob, the last row

    main_window._on_delete("Client", {})

    form = main_window._tabs_by_type["Client"].view.form
    assert form.form_inputs["Name"].text() == "Alice"
    assert main_window._selected_index_by_type["Client"] == 0


def test_delete_clamping_stays_within_the_same_record_type(main_window) -> None:
    """Selection lives in _records (mixed types), but the page-row position
    we clamp to is within the type-filtered list — so deleting a Client
    must never accidentally select an Airline at the same absolute index."""
    main_window._on_create("Airline", {"ID": "1", "Company Name": "Acme"})
    _seed_client(main_window, id_value="1", name="Alice")
    _seed_client(main_window, id_value="2", name="Bob")
    main_window._on_record_selected("Client", 0)  # Alice (abs idx 1)

    main_window._on_delete("Client", {})

    # The new selection must point to Bob, not the Airline at abs idx 0.
    selected = main_window._records[main_window._selected_index_by_type["Client"]]
    assert selected["Type"] == "Client"
    assert selected["Name"] == "Bob"


# ---------------------------------------------------------------------------
# Persistence failure — never let in-memory state move ahead of disk.
# ---------------------------------------------------------------------------


def test_save_failure_during_delete_leaves_records_untouched(
    main_window, monkeypatch
) -> None:
    from gui import main_window as mw

    _seed_client(main_window, id_value="1")
    _seed_client(main_window, id_value="2")
    main_window._on_record_selected("Client", 0)
    before = list(main_window._records)

    monkeypatch.setattr(
        mw,
        "save_records",
        lambda *a, **kw: (_ for _ in ()).throw(OSError("Disk full")),
    )
    main_window._on_delete("Client", {})

    assert main_window._records == before
    assert "Save failed:" in main_window.status._status_lbl.text()
    # Selection must NOT be cleared on failure — the user may want to retry.
    assert main_window._selected_index_by_type["Client"] == 0


def test_permission_error_during_delete_is_caught(main_window, monkeypatch) -> None:
    from gui import main_window as mw

    _seed_client(main_window, id_value="1")
    main_window._on_record_selected("Client", 0)

    monkeypatch.setattr(
        mw,
        "save_records",
        lambda *a, **kw: (_ for _ in ()).throw(PermissionError("read-only")),
    )
    main_window._on_delete("Client", {})  # must not propagate