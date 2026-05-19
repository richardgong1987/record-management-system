from dataclasses import dataclass

from record.service import AUTO_ID_TYPES, create_record, next_id
from record.use_cases.ports import Save
from record.use_cases.result import Err, Ok, Result
from record.use_cases.state import State
from record.validator import RecordValidationError, check_unique_id


@dataclass(frozen=True)
class CreateRecord:
    save: Save

    def __call__(self, record_type: str, payload: dict, state: State) -> Result:
        # Flow:
        # 1. Build & validate the new record (auto-ID, project, required, unique)
        # 2. Append to a fresh list
        # 3. Persist via the save port
        # 4. Return Ok / Err — selection is left untouched
        # Step 1: Build & validate
        try:
            record = self._build_record(record_type, payload, state.records)
        except RecordValidationError as exc:
            return Err(str(exc))

        # Step 2: Append to a fresh list (do not mutate the input)
        new_records = [*state.records, record]

        # Step 3: Persist
        try:
            self.save(new_records)
        except OSError as exc:
            return Err(f"Save failed: {exc}")

        # Step 4: Return success — selection unchanged
        return Ok(new_records, state.selected, f"Create {record_type}: {record}")

    @staticmethod
    def _build_record(record_type: str, payload: dict, records: list[dict]) -> dict:
        # ``next_id`` is inside the build step so a malformed existing ID in
        # the store surfaces as a ``RecordValidationError`` the caller
        # converts to a status message, not a GUI crash.
        if record_type in AUTO_ID_TYPES:
            payload = {**payload, "ID": str(next_id(records, record_type))}
        record = create_record(record_type, payload)
        check_unique_id(record, records)
        return record
