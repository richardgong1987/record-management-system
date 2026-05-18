import os

# Offscreen must be set before QApplication is imported.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication


def _client_payload(name: str = "Alice") -> dict:
    # ID intentionally omitted — Client IDs are auto-assigned on create and
    # preserved (not user-editable) on update, so the GUI form does not
    # collect one.
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
    _seed_client(main_window)
    before = list(main_window._records)

    main_window._on_update("Client", _client_payload(name="Mallory"))

    assert main_window._records == before
    assert "Select a record to update first." in main_window.status._status_lbl.text()


def test_update_with_stale_selection_is_treated_as_no_selection(
    main_window,
) -> None:
    _seed_client(main_window)
    # Force a selection that's no longer in _records (identity-check fails).
    main_window._selected_record_by_type["Client"] = {"Type": "Client", "stale": True}

    before = list(main_window._records)
    main_window._on_update("Client", _client_payload(name="Mallory"))

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

    window._on_create("Client", _client_payload(name="Alice"))
    window._on_record_selected("Client", 0)
    before = list(window._records)

    window._on_update("Client", _client_payload(name="Alicia"))

    assert window._records == before
    assert "Update cancelled." in window.status._status_lbl.text()


# ---------------------------------------------------------------------------
# Happy path — selecting a row, editing, and updating replaces in place.
# ---------------------------------------------------------------------------


def test_selecting_a_row_populates_the_form(main_window) -> None:
    _seed_client(main_window, name="Bob")
    main_window._on_record_selected("Client", 0)

    form = main_window._tabs_by_type["Client"].view.form
    # First seeded Client gets the auto-assigned ID 1.
    assert form.form_inputs["ID"].text() == "1"
    assert form.form_inputs["Name"].text() == "Bob"
    assert main_window._selected_record_by_type["Client"] is main_window._records[0]


def test_update_replaces_the_selected_record_in_place(main_window) -> None:
    _seed_client(main_window, name="Alice")
    _seed_client(main_window, name="Bob")
    assert len(main_window._records) == 2

    main_window._on_record_selected("Client", 0)
    main_window._on_update("Client", _client_payload(name="Alicia"))

    assert len(main_window._records) == 2  # no append
    assert main_window._records[0]["Name"] == "Alicia"
    assert main_window._records[1]["Name"] == "Bob"  # untouched


def test_update_persists_to_disk(main_window) -> None:
    from gui import main_window as mw

    _seed_client(main_window, name="Alice")
    main_window._on_record_selected("Client", 0)
    main_window._on_update("Client", _client_payload(name="Alicia"))

    import jsonlines

    with jsonlines.open(mw.DATA_FILE_PATH) as reader:
        on_disk = list(reader)
    assert on_disk == main_window._records
    assert on_disk[0]["Name"] == "Alicia"


@pytest.mark.parametrize(
    "record_type,seed_payload,update_payload,expected_field,expected_value",
    [
        pytest.param(
            "Airline",
            _airline_payload(company="Acme"),
            _airline_payload(company="Acme Aviation"),
            "Company Name",
            "Acme Aviation",
            id="airline",
        ),
        pytest.param(
            "Flight",
            _flight_payload(),
            _flight_payload(date="2026-07-04T12:00:00"),
            "Date",
            "2026-07-04T12:00:00",
            id="flight-no-own-id",
        ),
    ],
)
def test_update_works_for_record_type(
    main_window,
    record_type: str,
    seed_payload: dict,
    update_payload: dict,
    expected_field: str,
    expected_value: str,
) -> None:
    main_window._on_create(record_type, seed_payload)
    main_window._on_record_selected(record_type, 0)
    main_window._on_update(record_type, update_payload)

    assert main_window._records[-1][expected_field] == expected_value


# ---------------------------------------------------------------------------
# Validation — same pipeline as create; failures must not touch storage.
# ---------------------------------------------------------------------------


def test_update_with_empty_required_field_is_rejected(main_window) -> None:
    _seed_client(main_window)
    main_window._on_record_selected("Client", 0)

    before = list(main_window._records)
    main_window._on_update("Client", _client_payload(name=""))

    assert main_window._records == before


def test_update_with_empty_name_reports_required_message(main_window) -> None:
    # Pinned separately because we also want to assert the status-bar text,
    # not just that records are untouched.
    _seed_client(main_window)
    main_window._on_record_selected("Client", 0)

    main_window._on_update("Client", _client_payload(name=""))

    assert "Name is required." in main_window.status._status_lbl.text()


# ---------------------------------------------------------------------------
# ID preservation — the orchestrator overrides whatever ID the payload
# carries with the selected record's ID, so a tampered payload (e.g. a
# read-only widget bypass) cannot rename a record.
# ---------------------------------------------------------------------------


def test_update_preserves_existing_id_even_if_payload_carries_a_different_one(
    main_window,
) -> None:
    _seed_client(main_window, name="Alice")
    _seed_client(main_window, name="Bob")
    main_window._on_record_selected("Client", 0)
    original_id = main_window._records[0]["ID"]

    # Payload smuggles a different ID; orchestrator must ignore it.
    tampered = {**_client_payload(name="Alicia"), "ID": "999"}
    main_window._on_update("Client", tampered)

    assert main_window._records[0]["ID"] == original_id
    assert main_window._records[0]["Name"] == "Alicia"


# ---------------------------------------------------------------------------
# Persistence failure — never let in-memory state move ahead of disk.
#
# OSError and PermissionError (an OSError subclass) must both be caught
# by the orchestrator without propagating.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "exc",
    [
        pytest.param(OSError("Disk full"), id="disk-full-oserror"),
        pytest.param(PermissionError("read-only"), id="permission-error"),
    ],
)
def test_save_failure_during_update_leaves_records_untouched(
    main_window, monkeypatch, exc: OSError
) -> None:
    from gui import main_window as mw

    _seed_client(main_window, name="Alice")
    main_window._on_record_selected("Client", 0)
    before = list(main_window._records)

    def raise_exc(*_args, **_kwargs):
        raise exc

    monkeypatch.setattr(mw, "save_records", raise_exc)

    main_window._on_update("Client", _client_payload(name="Alicia"))

    assert main_window._records == before
    assert "Save failed:" in main_window.status._status_lbl.text()
