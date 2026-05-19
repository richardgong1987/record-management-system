from dataclasses import dataclass

from record.use_cases.ports import Confirm, Save
from record.use_cases.result import Cancelled, Err, Ok, Result
from record.use_cases.state import State


@dataclass(frozen=True)
class DeleteRecord:
    save: Save
    confirm: Confirm

    def __call__(self, record_type: str, _payload: dict, state: State) -> Result:
        # Flow:
        # 1. Guard against missing / stale selection
        # 2. Ask the user to confirm
        # 3. Capture the table-row position by identity (duplicate Flights
        #    must stay distinguishable) BEFORE filtering the list
        # 4. Build new_records without the deleted dict, persist
        # 5. Compute the next selection — the survivor at the same position,
        #    clamped to the new end of the list, or None if the tab emptied
        # Step 1: Selection guard
        record = state.selected
        if record is None:
            return Err("Select a record to delete first.")

        # Step 2: Confirm
        body = f"Delete this {record_type} record?\n\n{record}"
        if not self.confirm("Confirm delete", body):
            return Cancelled("Delete cancelled.")

        # Step 3: Capture position by identity
        type_records = [r for r in state.records if r["Type"] == record_type]
        position = next(i for i, r in enumerate(type_records) if r is record)

        # Step 4: Filter + persist
        new_records = [r for r in state.records if r is not record]
        try:
            self.save(new_records)
        except OSError as exc:
            return Err(f"Save failed: {exc}")

        # Step 5: Compute reselection + repaint the form to match
        new_selection = self._next_selection(new_records, record_type, position)
        return Ok(
            new_records,
            new_selection,
            f"Delete {record_type}: {record}",
            repaint_form=True,
        )

    @staticmethod
    def _next_selection(
        records: list[dict], record_type: str, deleted_position: int
    ) -> dict | None:
        survivors = [r for r in records if r["Type"] == record_type]
        if not survivors:
            return None
        return survivors[min(deleted_position, len(survivors) - 1)]
