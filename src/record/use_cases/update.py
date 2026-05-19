from dataclasses import dataclass

from record.service import AUTO_ID_TYPES, create_record
from record.use_cases.ports import Confirm, Save
from record.use_cases.result import Cancelled, Err, Ok, Result
from record.use_cases.state import State
from record.validator import RecordValidationError, check_unique_id


@dataclass(frozen=True)
class UpdateRecord:
    save: Save
    confirm: Confirm

    def __call__(self, record_type: str, payload: dict, state: State) -> Result:
        # Flow:
        # 1. Guard against missing / stale selection
        # 2. Preserve auto-IDs (the form can't change them)
        # 3. Build & validate against records EXCLUDING the selected one
        # 4. Ask the user to confirm the overwrite
        # 5. Build new_records by identity-replacement, persist, return Ok
        # Step 1: Selection guard
        if state.selected is None:
            return Err("Select a record to update first.")

        # Step 2: Preserve auto-IDs
        if record_type in AUTO_ID_TYPES:
            payload = {**payload, "ID": str(state.selected["ID"])}

        # Step 3: Validate against OTHERS so a no-op ID edit still passes
        try:
            record = create_record(record_type, payload)
            others = [r for r in state.records if r is not state.selected]
            check_unique_id(record, others)
        except RecordValidationError as exc:
            return Err(str(exc))

        # Step 4: Confirm
        body = f"Update this {record_type} record?\n\n{record}"
        if not self.confirm("Confirm update", body):
            return Cancelled("Update cancelled.")

        # Step 5: Build a fresh list, persist, only THEN signal new selection
        new_records = [record if r is state.selected else r for r in state.records]
        try:
            self.save(new_records)
        except OSError as exc:
            return Err(f"Save failed: {exc}")

        return Ok(new_records, record, f"Update {record_type}: {record}")
