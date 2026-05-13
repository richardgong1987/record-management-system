import os

# Offscreen must be set before QApplication is imported.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication


def _client_payload(id_value: str = "1") -> dict:
    return {
        "ID": id_value,
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


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def main_window(qapp, monkeypatch, tmp_path):
    # Redirect the data-file path to a per-test temp file so we don't touch
    # the real record store. Patch on the module before instantiating, since
    # MainWindow.__init__ reads DATA_FILE_PATH at construction time.
    from gui import main_window as mw

    monkeypatch.setattr(mw, "DATA_FILE_PATH", tmp_path / "record.jsonl")
    return mw.MainWindow()


# ---------------------------------------------------------------------------
# Successful save — the happy path is included so we know the test harness
# itself isn't masking the rollback signal in the failure test.
# ---------------------------------------------------------------------------


def test_successful_create_appends_record_to_memory(main_window) -> None:
    before = len(main_window._records)
    main_window._on_create("Client", _client_payload(id_value="99"))
    assert len(main_window._records) == before + 1
    assert main_window._records[-1]["ID"] == 99


# ---------------------------------------------------------------------------
# Save-failure rollback — the actual hotfix being verified.
# ---------------------------------------------------------------------------


def test_save_failure_rolls_back_in_memory_append(main_window, monkeypatch) -> None:
    from gui import main_window as mw

    def raise_disk_full(*_args, **_kwargs):
        raise OSError("Disk full")

    monkeypatch.setattr(mw, "save_records", raise_disk_full)

    before = len(main_window._records)

    # The orchestrator must NOT propagate the OSError — it catches it,
    # rolls back, and reports through the status bar.
    main_window._on_create("Client", _client_payload(id_value="42"))

    assert len(main_window._records) == before, (
        "Save failure must roll back the in-memory append so _records "
        "stays consistent with the on-disk file."
    )


def test_save_failure_does_not_raise(main_window, monkeypatch) -> None:
    from gui import main_window as mw

    monkeypatch.setattr(
        mw, "save_records", lambda *a, **kw: (_ for _ in ()).throw(PermissionError("ro"))
    )

    # PermissionError is a subclass of OSError — must be caught too.
    main_window._on_create("Client", _client_payload(id_value="43"))


def test_validation_failure_does_not_touch_records(main_window) -> None:
    before = len(main_window._records)
    # Empty ID — should be rejected before append, no rollback needed.
    main_window._on_create("Client", _client_payload(id_value=""))
    assert len(main_window._records) == before
