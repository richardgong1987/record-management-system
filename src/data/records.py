from pathlib import Path
import jsonlines

INTEGER_FIELDS = {"ID", "Client_ID", "Airline_ID"}
REQUIRED_FIELDS = {
    "Client": ["ID", "Name", "Address Line 1", "City", "Country", "Phone Number"],
    "Airline": ["ID", "Company Name"],
    "Flight": ["Client_ID", "Airline_ID", "Date", "Start City", "End City"],
}


class RecordValidationError(ValueError):
    """Raised when a record cannot be created."""


def create_record(record_type: str, payload: dict) -> dict:
    record = {"Type": record_type}

    for field, value in payload.items():
        if field in INTEGER_FIELDS:
            try:
                record[field] = int(value)
            except ValueError as exc:
                raise RecordValidationError(f"{field} must be a whole number.") from exc
        else:
            record[field] = value

    for field in REQUIRED_FIELDS[record_type]:
        if record.get(field) in ("", None, "-- select --"):
            raise RecordValidationError(f"{field} is required.")
    return record


def save_records(path: str, records: list[dict]) -> None:
    record_path = Path(path)
    record_path.parent.mkdir(parents=True, exist_ok=True)

    with jsonlines.open(record_path, mode="w") as writer:
        writer.write_all(records)


def load_records(path: str) -> list[dict]:
    record_path = Path(path)

    if not record_path.exists():
        return []

    with jsonlines.open(record_path) as reader:
        return list(reader)
