"""Record feature: validator, service, repository.

Public surface re-exported for convenient imports:

    from record import create_record, save_records, load_records
"""

from record.repository import load_records, save_records
from record.service import create_record
from record.validator import RecordValidationError, check_unique_id

__all__ = [
    "RecordValidationError",
    "check_unique_id",
    "create_record",
    "load_records",
    "save_records",
]
