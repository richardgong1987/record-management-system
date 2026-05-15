import os

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
    # Default confirmations to Yes so tests don't pop a real dialog.
    # Tests that want to simulate a No override this.
    monkeypatch.setattr(mw, "confirm", lambda *_a, **_k: True)
    return window


def _seed(window, record_type: str, **payload) -> dict:
    window._on_create(record_type, payload)
    return window._records[-1]


# ---------------------------------------------------------------------------
# Guard rails — empty source and declined confirmation.
# ---------------------------------------------------------------------------


def test_clear_with_no_records_of_that_type_skips_dialog(qapp, monkeypatch, tmp_path):
    """If there is nothing to clear we must NOT pop a confirmation dialog —
    asking 'are you sure?' about a no-op trains users to dismiss prompts."""
    from gui import main_window as mw

    monkeypatch.setattr(mw, "DATA_FILE_PATH", tmp_path / "record.jsonl")
    window = mw.MainWindow()

    confirm_calls = []
    monkeypatch.setattr(
        mw,
        "confirm",
        lambda *a, **k: confirm_calls.append((a, k)) or True,
    )

    window._on_clear_all("Client")

    assert confirm_calls == []
    assert "No Client records to clear." in window.status._status_lbl.text()


def test_declined_confirmation_leaves_records_untouched(
    qapp, monkeypatch, tmp_path
) -> None:
    from gui import main_window as mw

    monkeypatch.setattr(mw, "DATA_FILE_PATH", tmp_path / "record.jsonl")
    window = mw.MainWindow()
    monkeypatch.setattr(mw, "confirm", lambda *_a, **_k: False)

    window._on_create("Client", _client_payload(id_value="1"))
    before = list(window._records)

    window._on_clear_all("Client")

    assert window._records == before
    assert "Clear cancelled." in window.status._status_lbl.text()


# ---------------------------------------------------------------------------
# Happy path — drops every record of the active type, keeps the others.
# ---------------------------------------------------------------------------


def test_clear_removes_every_record_of_the_active_type(main_window) -> None:
    _seed(main_window, "Client", **_client_payload(id_value="1", name="Alice"))
    _seed(main_window, "Client", **_client_payload(id_value="2", name="Bob"))
    _seed(main_window, "Client", **_client_payload(id_value="3", name="Carol"))

    main_window._on_clear_all("Client")

    assert main_window._records == []
    assert "Cleared all Client records." in main_window.status._status_lbl.text()


def test_clear_keeps_records_of_other_types(main_window) -> None:
    _seed(main_window, "Client", **_client_payload(id_value="1"))
    _seed(main_window, "Airline", **_airline_payload(id_value="9", company="Acme"))
    _seed(main_window, "Flight", **_flight_payload())

    main_window._on_clear_all("Client")

    remaining_types = {r["Type"] for r in main_window._records}
    assert remaining_types == {"Airline", "Flight"}


def test_clear_persists_to_disk(main_window) -> None:
    from gui import main_window as mw

    _seed(main_window, "Client", **_client_payload(id_value="1"))
    _seed(main_window, "Airline", **_airline_payload(id_value="9"))
    main_window._on_clear_all("Client")

    import jsonlines

    with jsonlines.open(mw.DATA_FILE_PATH) as reader:
        on_disk = list(reader)
    assert on_disk == main_window._records
    assert all(r["Type"] != "Client" for r in on_disk)


def test_clear_writes_empty_file_when_only_type_in_store(main_window) -> None:
    from gui import main_window as mw

    _seed(main_window, "Airline", **_airline_payload(id_value="1"))
    _seed(main_window, "Airline", **_airline_payload(id_value="2", company="Beta"))

    main_window._on_clear_all("Airline")

    assert main_window._records == []
    assert mw.DATA_FILE_PATH.read_text() == ""


def test_clear_works_for_each_record_type(main_window) -> None:
    _seed(main_window, "Client", **_client_payload(id_value="1"))
    _seed(main_window, "Airline", **_airline_payload(id_value="1"))
    _seed(main_window, "Flight", **_flight_payload())

    main_window._on_clear_all("Flight")
    assert all(r["Type"] != "Flight" for r in main_window._records)

    main_window._on_clear_all("Airline")
    assert all(r["Type"] != "Airline" for r in main_window._records)

    main_window._on_clear_all("Client")
    assert main_window._records == []


# ---------------------------------------------------------------------------
# Post-clear state — form cleared, selection forgotten, other tabs untouched.
# ---------------------------------------------------------------------------


def test_clear_resets_form_and_selection_for_active_tab(main_window) -> None:
    _seed(main_window, "Client", **_client_payload(id_value="1", name="Alice"))
    main_window._on_record_selected("Client", 0)
    form = main_window._tabs_by_type["Client"].view.form
    assert form.form_inputs["Name"].text() == "Alice"
    assert main_window._selected_record_by_type["Client"] is main_window._records[0]

    main_window._on_clear_all("Client")

    assert main_window._selected_record_by_type["Client"] is None
    assert form.form_inputs["Name"].text() == ""


def test_clear_preserves_other_tab_selection_when_indices_shift(
    main_window,
) -> None:
    """Codex P2 regression: under the old absolute-index storage, clearing
    Clients (which sat at absolute indices 0 and 1) used to leave the
    Airline tab's stored index pointing at the wrong record (or out of
    bounds). With identity-based storage the Airline selection survives
    the list rewrite untouched."""
    _seed(main_window, "Client", **_client_payload(id_value="1"))
    _seed(main_window, "Client", **_client_payload(id_value="2"))
    _seed(main_window, "Airline", **_airline_payload(id_value="9", company="Acme"))

    main_window._on_record_selected("Airline", 0)
    airline_ref = main_window._selected_record_by_type["Airline"]
    assert airline_ref is main_window._records[2]  # abs idx 2 before clear

    main_window._on_clear_all("Client")

    # Airline record now sits at abs idx 0, but the stored selection still
    # resolves to the SAME dict (identity preserved across the rewrite).
    assert main_window._selected_record_by_type["Airline"] is airline_ref
    assert main_window._records[0] is airline_ref

    # And a subsequent delete on the Airline tab targets that same record.
    main_window._on_delete("Airline", {})
    assert all(r is not airline_ref for r in main_window._records)


def test_clear_does_not_touch_other_tabs_selection(main_window) -> None:
    """Codex P2 regression: clear-all rebuilds _records, so an absolute-index
    selection on another tab used to drift. Storing the dict reference keeps
    identity stable across the list rewrite."""
    _seed(main_window, "Client", **_client_payload(id_value="1"))
    _seed(main_window, "Airline", **_airline_payload(id_value="9", company="Acme"))
    main_window._on_record_selected("Airline", 0)
    airline_ref = main_window._selected_record_by_type["Airline"]

    main_window._on_clear_all("Client")

    # The selected Airline dict must be the SAME object — same identity, not
    # just same values — and must still be present in _records.
    assert main_window._selected_record_by_type["Airline"] is airline_ref
    assert any(r is airline_ref for r in main_window._records)
    airline_form = main_window._tabs_by_type["Airline"].view.form
    assert airline_form.form_inputs["Company Name"].text() == "Acme"


# ---------------------------------------------------------------------------
# Persistence failure — never let in-memory state move ahead of disk.
# ---------------------------------------------------------------------------


def test_save_failure_during_clear_leaves_records_untouched(
    main_window, monkeypatch
) -> None:
    from gui import main_window as mw

    _seed(main_window, "Client", **_client_payload(id_value="1"))
    before = list(main_window._records)

    monkeypatch.setattr(
        mw,
        "save_records",
        lambda *a, **k: (_ for _ in ()).throw(OSError("Disk full")),
    )
    main_window._on_clear_all("Client")

    assert main_window._records == before
    assert "Save failed:" in main_window.status._status_lbl.text()


def test_permission_error_during_clear_is_caught(main_window, monkeypatch) -> None:
    from gui import main_window as mw

    _seed(main_window, "Client", **_client_payload(id_value="1"))

    monkeypatch.setattr(
        mw,
        "save_records",
        lambda *a, **k: (_ for _ in ()).throw(PermissionError("read-only")),
    )
    main_window._on_clear_all("Client")  # must not propagate


# ---------------------------------------------------------------------------
# Wiring — the Clear button on the form fires clear_all_requested.
# ---------------------------------------------------------------------------


def test_clear_button_click_triggers_orchestrator(qapp, monkeypatch, tmp_path) -> None:
    """End-to-end signal wiring: pressing the Clear button on the form must
    route through BaseFormController -> TabController -> MainWindow and
    actually clear the active tab's records."""
    from gui import main_window as mw

    monkeypatch.setattr(mw, "DATA_FILE_PATH", tmp_path / "record.jsonl")
    window = mw.MainWindow()
    monkeypatch.setattr(mw, "confirm", lambda *_a, **_k: True)

    window._on_create("Client", _client_payload(id_value="1"))
    client_form = window._tabs_by_type["Client"].view.form

    client_form.clear_btn.click()

    assert window._records == []