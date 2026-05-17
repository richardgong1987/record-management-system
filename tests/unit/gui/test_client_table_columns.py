import os

# Offscreen must be set before QApplication is imported.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from gui.client.types import CLIENT_TABLE_COLUMNS


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_client_table_columns_include_country_after_zip_code() -> None:
    # Position matters: the brief lists Country immediately after Zip Code,
    # and the visible table column order mirrors that.
    assert "Country" in CLIENT_TABLE_COLUMNS
    zip_idx = CLIENT_TABLE_COLUMNS.index("Zip Code")
    country_idx = CLIENT_TABLE_COLUMNS.index("Country")
    assert country_idx == zip_idx + 1


def test_built_client_tab_renders_country_column(qapp, monkeypatch, tmp_path) -> None:
    # Build the real tab through tab_registry and confirm the rendered
    # QTableWidget has a Country header — guards against a future change
    # to RECORD_TYPES that accidentally swaps the column list back to
    # CLIENT_TEXT_FIELDS (which omits Country).
    from gui import main_window as mw

    monkeypatch.setattr(mw, "DATA_FILE_PATH", tmp_path / "record.jsonl")
    window = mw.MainWindow()
    table = window._tabs_by_type["Client"].view.record_list.table

    headers = [
        table.horizontalHeaderItem(i).text() for i in range(table.columnCount())
    ]
    assert "Country" in headers


def test_country_value_populates_into_client_row(
        qapp, monkeypatch, tmp_path
) -> None:
    # End-to-end check at the table level: a Client created with Country="USA"
    # must render "USA" in the Country column of its row.
    from gui import main_window as mw

    monkeypatch.setattr(mw, "DATA_FILE_PATH", tmp_path / "record.jsonl")
    monkeypatch.setattr(mw, "confirm", lambda *_a, **_k: True)
    window = mw.MainWindow()

    window._on_create(
        "Client",
        {
            "Name": "Alice",
            "Address Line 1": "1 Main St",
            "Address Line 2": "",
            "Address Line 3": "",
            "City": "NYC",
            "State": "NY",
            "Zip Code": "10001",
            "Country": "USA",
            "Phone Number": "555-0100",
        },
    )

    table = window._tabs_by_type["Client"].view.record_list.table
    country_col = next(
        i
        for i in range(table.columnCount())
        if table.horizontalHeaderItem(i).text() == "Country"
    )
    assert table.item(0, country_col).text() == "USA"
