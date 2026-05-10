"""Record creation service.

Composes parsing, projection, and validation into a single
``create_record`` use-case. No I/O — that lives in ``repository``.

NOTE: the GUI ``*_TEXT_FIELDS`` imports below are a layering inversion
(data depends on GUI). They are kept for step 1 of the refactor only;
step 2 will move the field schemas onto the data side and flip the arrow.
"""

from data.record.validator import RecordValidationError, check_required
from gui.airline.types import AIRLINE_TEXT_FIELDS
from gui.client.types import CLIENT_TEXT_FIELDS
from gui.flight.types import FLIGHT_TEXT_FIELDS

INTEGER_FIELDS = ("ID", "Client_ID", "Airline_ID")

ALLOWED_FIELDS = {
    "Client": CLIENT_TEXT_FIELDS,
    "Airline": AIRLINE_TEXT_FIELDS,
    "Flight": FLIGHT_TEXT_FIELDS,
}


def create_record(record_type: str, payload: dict) -> dict:
    if record_type not in ALLOWED_FIELDS:
        raise RecordValidationError(f"Unknown record type: {record_type}.")

    record = _project_payload(record_type, payload)
    check_required(record_type, record)
    _coerce_integers(record)
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
        try:
            record[field] = int(record[field])
        except (TypeError, ValueError) as exc:
            raise RecordValidationError(f"{field} must be a whole number.") from exc
