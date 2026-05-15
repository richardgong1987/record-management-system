import jsonlines
import pytest

from record.repository import load_records, save_records


CLIENT_RECORD = {"Type": "Client", "ID": 1, "Name": "Arjun"}
AIRLINE_RECORD = {"Type": "Airline", "ID": 2, "Company Name": "British Airways"}
FLIGHT_RECORD = {
    "Type": "Flight",
    "Client_ID": 1,
    "Airline_ID": 2,
    "Date": "2026-05-13T14:30:00",
    "Start City": "London",
    "End City": "Tokyo",
}


@pytest.mark.parametrize(
    "prepare_file",
    [
        pytest.param(lambda path: None, id="missing-file"),
        pytest.param(
            lambda path: path.write_text("", encoding="utf-8"),
            id="empty-file",
        ),
    ],
)
def test_load_records_returns_empty_list(tmp_path, prepare_file) -> None:
    path = tmp_path / "records.jsonl"
    prepare_file(path)

    assert load_records(path) == []


@pytest.mark.parametrize(
    "records",
    [
        pytest.param([], id="empty-list"),
        pytest.param([CLIENT_RECORD], id="single-client"),
        pytest.param([CLIENT_RECORD, AIRLINE_RECORD, FLIGHT_RECORD], id="mixed-types"),
    ],
)
def test_save_then_load_round_trip(tmp_path, records) -> None:
    path = tmp_path / "records.jsonl"

    save_records(path, records)

    assert load_records(path) == records


def test_save_records_overwrites_existing_file(tmp_path) -> None:
    path = tmp_path / "records.jsonl"
    save_records(path, [CLIENT_RECORD, AIRLINE_RECORD])

    save_records(path, [FLIGHT_RECORD])

    assert load_records(path) == [FLIGHT_RECORD]


def test_save_records_creates_parent_directory(tmp_path) -> None:
    path = tmp_path / "nested" / "records.jsonl"

    save_records(path, [CLIENT_RECORD])

    assert path.exists()
    assert load_records(path) == [CLIENT_RECORD]


def test_save_records_leaves_no_temp_file(tmp_path) -> None:
    # save_records writes to a sibling .tmp and os.replace()s it; the temp
    # file must not linger after a successful write.
    path = tmp_path / "records.jsonl"

    save_records(path, [CLIENT_RECORD])

    assert list(tmp_path.glob("*.tmp")) == []


def test_load_records_raises_invalid_line_error_for_malformed_jsonl(tmp_path) -> None:
    path = tmp_path / "records.jsonl"
    path.write_text("not valid json\n", encoding="utf-8")

    with pytest.raises(jsonlines.InvalidLineError):
        load_records(path)
