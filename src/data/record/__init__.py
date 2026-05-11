"""Record feature: validator, service, repository.

Public surface re-exported for convenient imports:

    from data.record import create_record, save_records, load_records
"""

from data.record.repository import load_records, save_records
from data.record.service import create_record
from data.record.validator import RecordValidationError, check_unique_id

__all__ = [
    "RecordValidationError",
    "check_unique_id",
    "create_record",
    "load_records",
    "save_records",
]
