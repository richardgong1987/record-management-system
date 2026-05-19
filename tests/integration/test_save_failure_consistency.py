"""Save-failure consistency through MainWindow.

When ``save_records`` raises ``OSError`` mid-update or mid-delete,
``MainWindow._records`` must not move ahead of the on-disk file —
otherwise a subsequent successful save would write a list disk never
saw. The existing unit suite covers the create rollback; this test
covers update and delete, where the failure mode is "don't reassign
``self._records``" rather than "pop the appended record".

See docs/design/integration-tests.md for the test taxonomy and
docs/design/update-record.md / delete-record.md for the flows under test.
"""

import os

# Offscreen must be set before QApplication is imported.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from record.repository import load_records


def _client_payload(name: str = "Alice") -> dict:
    # ID intentionally omitted — auto-assigned by the orchestrator.
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


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def main_window(qapp, monkeypatch, tmp_path):
    # Same shape as the existing GUI fixtures: redirect the data file to
    # tmp_path and default confirm() to Yes so the update/delete flows
    # don't pop a real QMessageBox.
    from gui import main_window as mw

    monkeypatch.setattr(mw, "DATA_FILE_PATH", tmp_path / "record.jsonl")
    monkeypatch.setattr(mw, "confirm", lambda *_a, **_k: True)
    return mw.MainWindow()


def _seed_two_clients(window) -> tuple[dict, dict]:
    window._on_create("Client", _client_payload(name="Alice"))
    window._on_create("Client", _client_payload(name="Bob"))
    return window._records[0], window._records[1]


def _break_save(monkeypatch, exc: OSError) -> None:
    # Patch the symbol on the gui.main_window module, not on
    # record.repository, because main_window imported save_records by name.
    from gui import main_window as mw

    def raise_exc(*_args, **_kwargs):
        raise exc

    monkeypatch.setattr(mw, "save_records", raise_exc)


# ---------------------------------------------------------------------------
# Update — failure must leave _records and disk pointing at the prior state.
# ---------------------------------------------------------------------------


def test_update_save_failure_keeps_in_memory_in_sync_with_disk(
    main_window, monkeypatch
) -> None:
    from gui import main_window as mw

    alice, _bob = _seed_two_clients(main_window)
    main_window._selected_record_by_type["Client"] = alice
    disk_path = mw.DATA_FILE_PATH
    disk_before = load_records(disk_path)

    _break_save(monkeypatch, OSError("Disk full"))
    main_window._on_update("Client", _client_payload(name="Alicia"))

    # In-memory list still equals what disk holds — the rollback worked.
    assert main_window._records == disk_before
    assert load_records(disk_path) == disk_before


def test_update_save_failure_does_not_advance_selected_record(
    main_window, monkeypatch
) -> None:
    alice, _bob = _seed_two_clients(main_window)
    main_window._selected_record_by_type["Client"] = alice

    _break_save(monkeypatch, PermissionError("read-only"))
    main_window._on_update("Client", _client_payload(name="Alicia"))

    # The orchestrator only reassigns _selected_record_by_type after a
    # successful save — a failed save must leave the old reference in place.
    assert main_window._selected_record_by_type["Client"] is alice


# ---------------------------------------------------------------------------
# Delete — failure must leave _records and disk pointing at the prior state.
# ---------------------------------------------------------------------------


def test_delete_save_failure_keeps_in_memory_in_sync_with_disk(
    main_window, monkeypatch
) -> None:
    from gui import main_window as mw

    alice, _bob = _seed_two_clients(main_window)
    main_window._selected_record_by_type["Client"] = alice
    disk_path = mw.DATA_FILE_PATH
    disk_before = load_records(disk_path)

    _break_save(monkeypatch, OSError("Disk full"))
    main_window._on_delete("Client", {})

    assert main_window._records == disk_before
    assert load_records(disk_path) == disk_before


def test_delete_save_failure_preserves_record_count(
    main_window, monkeypatch
) -> None:
    alice, _bob = _seed_two_clients(main_window)
    main_window._selected_record_by_type["Client"] = alice
    before = len(main_window._records)

    _break_save(monkeypatch, OSError("Disk full"))
    main_window._on_delete("Client", {})

    assert len(main_window._records) == before
