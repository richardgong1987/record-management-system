import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def _client_payload(id_value: str, name: str = "Alice") -> dict:
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


# ---------------------------------------------------------------------------
# RecordListController: cellClicked → record_selected wiring.
#
# Use cellClicked (not itemSelectionChanged) so a re-click on the row index
# that previously held a now-deleted record still fires. Verified here at
# the controller level, decoupled from MainWindow.
# ---------------------------------------------------------------------------


def test_cellclicked_emits_record_selected_with_row(qapp) -> None:
    from gui.record_list.controller import RecordListController
    from gui.record_list.view import RecordListView

    view = RecordListView(["ID", "Name"])
    view.set_rows([{"ID": "1", "Name": "Alice"}, {"ID": "2", "Name": "Bob"}])
    ctrl = RecordListController(view)

    emissions: list[int] = []
    ctrl.record_selected.connect(emissions.append)

    view.table.cellClicked.emit(1, 0)
    assert emissions == [1]


def test_clicking_the_same_row_twice_emits_each_time(qapp) -> None:
    """Regression: the previous implementation listened on
    itemSelectionChanged, which Qt suppresses when the selection state
    is unchanged. After a delete, re-clicking the now-row-0 record was
    silently swallowed and the orchestrator never learned about it."""
    from gui.record_list.controller import RecordListController
    from gui.record_list.view import RecordListView

    view = RecordListView(["ID", "Name"])
    view.set_rows([{"ID": "1", "Name": "Alice"}])
    ctrl = RecordListController(view)

    emissions: list[int] = []
    ctrl.record_selected.connect(emissions.append)

    view.table.cellClicked.emit(0, 0)
    view.table.cellClicked.emit(0, 0)
    assert emissions == [0, 0]


# ---------------------------------------------------------------------------
# End-to-end regression for the user-reported bug:
#
#   "When I select the first one to delete, then the next one becomes the
#    first one, then I can not delete it."
#
# This test routes the click through the real Qt signal so the bug would
# reappear if cellClicked were swapped back to itemSelectionChanged.
# ---------------------------------------------------------------------------


def test_consecutive_deletes_via_row_zero_click(qapp, monkeypatch, tmp_path) -> None:
    from gui import main_window as mw

    monkeypatch.setattr(mw, "DATA_FILE_PATH", tmp_path / "record.jsonl")
    window = mw.MainWindow()
    monkeypatch.setattr(mw, "confirm", lambda *_a, **_k: True)

    window._on_create("Client", _client_payload(id_value="1", name="Alice"))
    window._on_create("Client", _client_payload(id_value="2", name="Bob"))

    table = window._tabs_by_type["Client"].view.record_list.table

    # Step 1: click row 0 (Alice) and delete.
    table.cellClicked.emit(0, 0)
    assert window._selected_index_by_type["Client"] == 0
    window._on_delete("Client", {})
    assert len(window._records) == 1
    assert window._records[0]["Name"] == "Bob"

    # Step 2: click row 0 again — this is now Bob, formerly row 1.
    # With itemSelectionChanged this click was swallowed; with cellClicked
    # it must propagate every time.
    table.cellClicked.emit(0, 0)
    assert window._selected_index_by_type["Client"] == 0

    # Step 3: delete must succeed, leaving no records.
    window._on_delete("Client", {})
    assert window._records == []
    assert "Delete Client" in window.status._status_lbl.text()