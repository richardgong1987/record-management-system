"""Record creation service.

Composes payload projection, required-field validation, and integer
coercion into a single ``create_record`` use-case. No I/O — that lives
in ``repository``. No GUI imports — the canonical field schemas live
in ``schema``.
"""

from data.record.schema import ALLOWED_FIELDS, INTEGER_FIELDS
from data.record.validator import (
    RecordValidationError,
    check_positive_integers,
    check_flight_date,
    check_required,
)


def create_record(record_type: str, payload: dict) -> dict:
    if record_type not in ALLOWED_FIELDS:
        raise RecordValidationError(f"Unknown record type: {record_type}.")

    record = _project_payload(record_type, payload)
    _coerce_integers(record)
    
    check_required(record_type, record)
    check_positive_integers(record)
    check_flight_date(record)
    return record

def _project_payload(record_type: str, payload: dict) -> dict:
    record = {"Type": record_type}
    for field in ALLOWED_FIELDS[record_type]:
        record[field] = payload.get(field, "")
    return record


def _coerce_integers(record: dict) -> None:
    for field in INTEGER_FIELDS:
        if field not in record:
            continue
        value = record[field]
        # Skip empty values — check_required runs next and raises a clearer
        # "<field> is required" error; non-required empty fields stay as "".
        if value in (None, ""):
            continue
        try:
            record[field] = int(value)
        except (TypeError, ValueError) as exc:
            raise RecordValidationError(f"{field} must be a whole number.") from exc
