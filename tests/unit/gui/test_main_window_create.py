import os

# Offscreen must be set before QApplication is imported.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication


def _client_payload(name: str = "Alice") -> dict:
    # ID intentionally omitted — Client IDs are auto-assigned by the
    # orchestrator before validation; the GUI form does not collect one.
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
    main_window._on_create("Client", _client_payload())
    assert len(main_window._records) == before + 1
    # First Client in an empty store gets the auto-assigned ID 1.
    assert main_window._records[-1]["ID"] == 1


def test_consecutive_creates_assign_sequential_ids(main_window) -> None:
    main_window._on_create("Client", _client_payload(name="Alice"))
    main_window._on_create("Client", _client_payload(name="Bob"))
    main_window._on_create("Client", _client_payload(name="Carol"))

    ids = [r["ID"] for r in main_window._records]
    assert ids == [1, 2, 3]


def test_auto_id_is_per_record_type(main_window) -> None:
    # Client and Airline number independently — first of each gets ID 1.
    main_window._on_create("Client", _client_payload())
    main_window._on_create("Airline", {"Company Name": "Acme"})

    client = next(r for r in main_window._records if r["Type"] == "Client")
    airline = next(r for r in main_window._records if r["Type"] == "Airline")
    assert client["ID"] == 1
    assert airline["ID"] == 1


# ---------------------------------------------------------------------------
# Save-failure rollback — the actual hotfix being verified.
#
# OSError and PermissionError (an OSError subclass) must both be caught
# by the orchestrator: rolled back in memory and reported through the
# status bar, never re-raised.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "exc",
    [
        pytest.param(OSError("Disk full"), id="disk-full-oserror"),
        pytest.param(PermissionError("read-only"), id="permission-error"),
    ],
)
def test_save_failure_rolls_back_in_memory_append(
    main_window, monkeypatch, exc: OSError
) -> None:
    from gui import main_window as mw

    def raise_exc(*_args, **_kwargs):
        raise exc

    monkeypatch.setattr(mw, "save_records", raise_exc)
    before = len(main_window._records)

    # The orchestrator must NOT propagate the OSError — it catches it,
    # rolls back, and reports through the status bar.
    main_window._on_create("Client", _client_payload())

    assert len(main_window._records) == before, (
        "Save failure must roll back the in-memory append so _records "
        "stays consistent with the on-disk file."
    )


def test_validation_failure_does_not_touch_records(main_window) -> None:
    before = len(main_window._records)
    # Empty Name — required field check rejects before append, no rollback.
    # ID can no longer be the trigger here: it is auto-assigned by the
    # orchestrator before validation runs.
    main_window._on_create("Client", _client_payload(name=""))
    assert len(main_window._records) == before
