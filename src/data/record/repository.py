"""JSONL persistence for records.

Persistence only — no validation, no business logic, no GUI.
"""

import os
from pathlib import Path

import jsonlines


def save_records(path: Path, records: list[dict]) -> None:
    record_path = Path(path)
    record_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = record_path.with_suffix(record_path.suffix + ".tmp")

    with jsonlines.open(tmp_path, mode="w") as writer:
        writer.write_all(records)
    os.replace(tmp_path, record_path)


def load_records(path: Path) -> list[dict]:
    record_path = Path(path)
    if not record_path.exists():
        return []
    with jsonlines.open(record_path) as reader:
        return list(reader)
