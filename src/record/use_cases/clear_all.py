from dataclasses import dataclass

from record.use_cases.ports import Confirm, Save
from record.use_cases.result import Cancelled, Err, Ok, Result
from record.use_cases.state import State


@dataclass(frozen=True)
class ClearAllRecords:
    save: Save
    confirm: Confirm

    def __call__(self, record_type: str, state: State) -> Result:
        # Flow:
        # 1. Refuse if the tab is already empty
        # 2. Ask the user to confirm
        # 3. Filter out every record of this type, persist
        # 4. Return Ok with cleared selection + form repaint
        # Step 1: Empty guard
        if not any(r["Type"] == record_type for r in state.records):
            return Err(f"No {record_type} records to clear.")

        # Step 2: Confirm
        body = f"Delete ALL {record_type} records?\n\nThis cannot be undone."
        if not self.confirm("Confirm clear all", body):
            return Cancelled("Clear cancelled.")

        # Step 3: Filter + persist. Other-type records keep their identity
        # through the comprehension, so other tabs' selections survive.
        new_records = [r for r in state.records if r["Type"] != record_type]
        try:
            self.save(new_records)
        except OSError as exc:
            return Err(f"Save failed: {exc}")

        # Step 4: Tab is now empty — drop selection and ask the View to clear
        return Ok(
            new_records,
            None,
            f"Cleared all {record_type} records.",
            repaint_form=True,
        )
