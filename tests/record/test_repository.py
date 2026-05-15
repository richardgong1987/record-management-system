import pytest
from record.repository import load_records, save_records


def test_load_records_returns_empty_list_when_file_missing(tmp_path) -> None:
    path = tmp_path / "records.jsonl"

    assert load_records(path) == []


def test_save_records_then_load_records_returns_same_records(tmp_path) -> None:
    path = tmp_path / "records.jsonl"
    records = [
        {"Type": "Client", "ID": 1, "Name": "Arjun"},
        {"Type": "Airline", "ID": 2, "Company Name": "British Airways"},
    ]

    save_records(path, records)

    assert load_records(path) == records


def test_load_records_returns_empty_list_for_empty_file(tmp_path) -> None:
    path = tmp_path / "records.jsonl"
    path.write_text("", encoding="utf-8")

    assert load_records(path) == []


def test_load_records_raises_for_invalid_json(tmp_path) -> None:
    path = tmp_path / "records.jsonl"
    path.write_text("not valid json\n", encoding="utf-8")

    with pytest.raises(Exception):
        load_records(path)


def test_save_records_creates_parent_directory(tmp_path) -> None:
    path = tmp_path / "nested" / "records.jsonl"
    records = [{"Type": "Client", "ID": 1, "Name": "Arjun"}]

    save_records(path, records)

    assert path.exists()
    assert load_records(path) == records
