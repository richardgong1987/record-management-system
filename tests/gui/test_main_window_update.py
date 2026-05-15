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


def _flight_payload(
    client_id: str = "1",
    airline_id: str = "2",
    date: str = "2026-06-01T09:00:00",
) -> dict:
    return {
        "Client_ID": client_id,
        "Airline_ID": airline_id,
        "Date": date,
        "Start City": "NYC",
        "End City": "LAX",
    }


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def main_window(qapp, monkeypatch, tmp_path):
    # Redirect the data-file path to a per-test temp file so tests never
    # touch the real record store. Default the confirmation dialog to Yes
    # so existing update tests don't pop a real QMessageBox.
    from gui import main_window as mw

    monkeypatch.setattr(mw, "DATA_FILE_PATH", tmp_path / "record.jsonl")
    monkeypatch.setattr(mw, "confirm", lambda *_a, **_k: True)
    return mw.MainWindow()


def _seed_client(window, **overrides) -> dict:
    """Push a Client record through the real create path so the table,
    selection, and on-disk file all line up the way the user would see them."""
    window._on_create("Client", _client_payload(**overrides))
    return window._records[-1]


# ---------------------------------------------------------------------------
# Guard rail: clicking Update without a selection must not touch anything.
# ---------------------------------------------------------------------------


def test_update_without_selection_reports_required_message(main_window) -> None:
    _seed_client(main_window, id_value="1")
    before = list(main_window._records)

    main_window._on_update("Client", _client_payload(id_value="1", name="Mallory"))

    assert main_window._records == before
    assert "Select a record to update first." in main_window.status._status_lbl.text()


def test_update_with_stale_selection_index_is_treated_as_no_selection(
    main_window,
) -> None:
    _seed_client(main_window, id_value="1")
    # Force a selection past the end of the records list.
    main_window._selected_index_by_type["Client"] = 99

    before = list(main_window._records)
    main_window._on_update("Client", _client_payload(id_value="1", name="Mallory"))

    assert main_window._records == before


# ---------------------------------------------------------------------------
# Confirmation — Update is destructive in the sense that it overwrites the
# previous record, so the orchestrator routes through the same confirm()
# helper as Delete and Clear. The fixture defaults the dialog to Yes;
# this test overrides it to No.
# ---------------------------------------------------------------------------


def test_declined_confirmation_leaves_records_untouched(
    qapp, monkeypatch, tmp_path
) -> None:
    from gui import main_window as mw

    monkeypatch.setattr(mw, "DATA_FILE_PATH", tmp_path / "record.jsonl")
    monkeypatch.setattr(mw, "confirm", lambda *_a, **_k: False)
    window = mw.MainWindow()

    window._on_create("Client", _client_payload(id_value="1", name="Alice"))
    window._on_record_selected("Client", 0)
    before = list(window._records)

    window._on_update("Client", _client_payload(id_value="1", name="Alicia"))

    assert window._records == before
    assert "Update cancelled." in window.status._status_lbl.text()


# ---------------------------------------------------------------------------
# Happy path — selecting a row, editing, and updating replaces in place.
# ---------------------------------------------------------------------------


def test_selecting_a_row_populates_the_form(main_window) -> None:
    _seed_client(main_window, id_value="7", name="Bob")
    main_window._on_record_selected("Client", 0)

    form = main_window._tabs_by_type["Client"].view.form
    assert form.form_inputs["ID"].text() == "7"
    assert form.form_inputs["Name"].text() == "Bob"
    assert main_window._selected_index_by_type["Client"] == 0


def test_update_replaces_the_selected_record_in_place(main_window) -> None:
    _seed_client(main_window, id_value="1", name="Alice")
    _seed_client(main_window, id_value="2", name="Bob")
    assert len(main_window._records) == 2

    main_window._on_record_selected("Client", 0)
    main_window._on_update("Client", _client_payload(id_value="1", name="Alicia"))

    assert len(main_window._records) == 2  # no append
    assert main_window._records[0]["Name"] == "Alicia"
    assert main_window._records[1]["Name"] == "Bob"  # untouched


def test_update_persists_to_disk(main_window) -> None:
    from gui import main_window as mw

    _seed_client(main_window, id_value="1", name="Alice")
    main_window._on_record_selected("Client", 0)
    main_window._on_update("Client", _client_payload(id_value="1", name="Alicia"))

    import jsonlines

    with jsonlines.open(mw.DATA_FILE_PATH) as reader:
        on_disk = list(reader)
    assert on_disk == main_window._records
    assert on_disk[0]["Name"] == "Alicia"


def test_update_works_for_airline_records(main_window) -> None:
    main_window._on_create("Airline", _airline_payload(id_value="1", company="Acme"))
    main_window._on_record_selected("Airline", 0)
    main_window._on_update(
        "Airline", _airline_payload(id_value="1", company="Acme Aviation")
    )
    assert main_window._records[-1]["Company Name"] == "Acme Aviation"


def test_update_works_for_flight_records_which_have_no_own_id(main_window) -> None:
    main_window._on_create("Flight", _flight_payload())
    main_window._on_record_selected("Flight", 0)
    main_window._on_update(
        "Flight", _flight_payload(date="2026-07-04T12:00:00")
    )
    assert main_window._records[-1]["Date"] == "2026-07-04T12:00:00"


# ---------------------------------------------------------------------------
# Validation — same pipeline as create; failures must not touch storage.
# ---------------------------------------------------------------------------


def test_update_with_empty_required_field_is_rejected(main_window) -> None:
    _seed_client(main_window, id_value="1")
    main_window._on_record_selected("Client", 0)

    before = list(main_window._records)
    main_window._on_update("Client", _client_payload(id_value="1", name=""))

    assert main_window._records == before
    assert "Name is required." in main_window.status._status_lbl.text()


def test_update_with_non_integer_id_is_rejected(main_window) -> None:
    _seed_client(main_window, id_value="1")
    main_window._on_record_selected("Client", 0)

    before = list(main_window._records)
    main_window._on_update("Client", _client_payload(id_value="abc"))

    assert main_window._records == before


# ---------------------------------------------------------------------------
# Uniqueness — excluding the record being updated, not the full list.
# ---------------------------------------------------------------------------


def test_update_allows_keeping_the_same_id(main_window) -> None:
    """A no-op ID edit must NOT trip the uniqueness check; otherwise no
    update on Client/Airline would ever succeed without renaming."""
    _seed_client(main_window, id_value="1")
    main_window._on_record_selected("Client", 0)
    main_window._on_update("Client", _client_payload(id_value="1", name="Renamed"))

    assert main_window._records[0]["Name"] == "Renamed"


def test_update_rejects_collision_with_another_records_id(main_window) -> None:
    _seed_client(main_window, id_value="1", name="Alice")
    _seed_client(main_window, id_value="2", name="Bob")
    main_window._on_record_selected("Client", 0)

    before = list(main_window._records)
    # Try to change Alice's ID to 2 — Bob already has it.
    main_window._on_update("Client", _client_payload(id_value="2", name="Alice"))

    assert main_window._records == before
    assert "already exists" in main_window.status._status_lbl.text()


# ---------------------------------------------------------------------------
# Persistence failure — never let in-memory state move ahead of disk.
# ---------------------------------------------------------------------------


def test_save_failure_during_update_leaves_records_untouched(
    main_window, monkeypatch
) -> None:
    from gui import main_window as mw

    _seed_client(main_window, id_value="1", name="Alice")
    main_window._on_record_selected("Client", 0)
    before = list(main_window._records)

    def raise_disk_full(*_args, **_kwargs):
        raise OSError("Disk full")

    monkeypatch.setattr(mw, "save_records", raise_disk_full)

    main_window._on_update("Client", _client_payload(id_value="1", name="Alicia"))

    assert main_window._records == before
    assert "Save failed:" in main_window.status._status_lbl.text()


def test_permission_error_during_update_is_caught(main_window, monkeypatch) -> None:
    from gui import main_window as mw

    _seed_client(main_window, id_value="1")
    main_window._on_record_selected("Client", 0)

    monkeypatch.setattr(
        mw,
        "save_records",
        lambda *a, **kw: (_ for _ in ()).throw(PermissionError("read-only")),
    )
    # PermissionError is an OSError subclass — must not propagate.
    main_window._on_update("Client", _client_payload(id_value="1", name="Alicia"))