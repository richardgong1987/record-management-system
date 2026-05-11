"""Record validation rules.

Pure functions — no I/O, no GUI, no global mutable state.
Validators raise ``RecordValidationError`` on failure and return ``None`` on success.
"""

REQUIRED_FIELDS = {
    "Client": ("ID", "Name", "Address Line 1", "City", "Country", "Phone Number"),
    "Airline": ("ID", "Company Name"),
    "Flight": ("Client_ID", "Airline_ID", "Date", "Start City", "End City"),
}

# The "-- select --" entry is the unselected placeholder of the Country combo box.
# Treating it as empty here prevents the literal label from being persisted.
_EMPTY_VALUES = ("", None, "-- select --")


class RecordValidationError(ValueError):
    """Raised when a record fails validation."""


def check_required(record_type: str, record: dict) -> None:
    for field in REQUIRED_FIELDS.get(record_type, ()):
        if record.get(field) in _EMPTY_VALUES:
            raise RecordValidationError(f"{field} is required.")


def check_unique_id(record: dict, existing: list[dict]) -> None:
    id_field = _id_field_for(record.get("Type", ""))
    if id_field is None:
        return

    new_id = record.get(id_field)
    for other in existing:
        if other.get("Type") != record["Type"]:
            continue
        if other.get(id_field) == new_id:
            raise RecordValidationError(
                f"{record['Type']} {id_field} {new_id} already exists."
            )


def _id_field_for(record_type: str) -> str | None:
    if record_type in ("Client", "Airline"):
        return "ID"
    return None
