# How deleting a record works

Design doc and tour for the delete-record flow. Covers the §15.2 sections (problem, data flow, mermaid diagram, module design, edge cases, error handling) and a walkthrough for teammates picking up the code.

Companion to [`create-record.md`](create-record.md) and [`update-record.md`](update-record.md) — read those first if you haven't, because delete reuses the same selection bookkeeping and the same atomic-write discipline.

---

## What it does

Click a row in the record table on the right → click **Delete** → a confirmation dialog asks "Delete this Client record? …" → confirm:

1. the row is removed from the in-memory list at the selected index,
2. the JSONL file is rewritten atomically with the survivors,
3. the table on the right refreshes,
4. the selection clamps to the same table-row position in the new list (the formerly-next record now sits at the deleted slot), and the form is re-populated with that record so clicking Delete again removes it too.

If no records of that type remain, the form is cleared and the selection is forgotten.

If the user declines the confirmation, nothing changes and the status bar says so. If the user clicks Delete without first selecting a row, the status bar shows a prompt and nothing else happens. If the disk write fails, the in-memory list is left untouched and the status bar shows the reason.

---

## Problem description

- **Problem**: users need to remove stored records when they are no longer relevant (a client leaving the agency, a cancelled flight, a duplicate row created by accident). Without a delete action, the only way to remove a row is editing `record.jsonl` by hand — which is exactly the kind of manual data-file editing this app is meant to avoid.
- **Expected input**: a row selection in the visible table plus a click on the Delete button, followed by a Yes/No on the confirmation dialog.
- **Expected output**: the targeted record is gone from `record.jsonl`; all other records are untouched; the table reflects the change; the form and selection state are reset so the user does not accidentally re-edit (or re-delete) a record that no longer exists.

---

## Data Flow

Delete is short — there is no parsing or validation of new field values, because the operation removes a record rather than producing one. The pipeline degenerates to **Reader → Confirmer → Repository**:

```
RecordListView.cellClicked            → Reader      (row click → stored absolute index; fires on every click so re-clicking the same row index after a refresh still propagates)
BaseFormView.delete_btn.clicked       → Reader      (intent to delete; no payload needed)
gui.common.dialogs.confirm            → Confirmer   (modal Yes/No)
MainWindow._on_delete                 → Orchestrator (build survivor list, save, swap)
save_records                          → Repository  (atomic JSONL write)
```

`confirm` is the only piece of UI in the pipeline that does not exist for create or update. It is a thin wrapper around `QMessageBox.question` in `src/gui/common/dialogs.py`, shared with `_on_clear_all`. Tests monkey-patch the module-level name (`gui.main_window.confirm`) with a deterministic Yes/No.

---

## Mermaid Flow Diagram

```mermaid
flowchart TD
    A[User clicks a row in the table] --> B[selection stored as absolute index]
    B --> C[User clicks Delete on the form]
    C --> D[BaseFormController.delete_requested]
    D --> E[TabController re-emits with record_type]
    E --> F[MainWindow._on_delete]
    F --> G{Selection present and in range?}
    G -- No --> H[StatusBar: 'Select a record to delete first.']
    G -- Yes --> I[confirm shows Yes/No dialog]
    I --> J{User confirmed?}
    J -- No --> K[StatusBar: 'Delete cancelled.']
    J -- Yes --> L[new_records = _records without the selected index]
    L --> M[save_records: tmp + os.replace]
    M --> N{OSError?}
    N -- Yes --> O[StatusBar: 'Save failed: ...',<br/>in-memory state unchanged]
    N -- No --> P[Swap _records, clear selection,<br/>clear form, refresh tables, status: 'Delete Client {...}']
```

---

## Module Design

The dependency arrow still points one way — GUI → record — and `record.*` has zero `from gui.*` imports.

### GUI side (Reader + Confirmer + Orchestrator)

| Module | Responsibility | Input | Output |
| --- | --- | --- | --- |
| `gui.common.BaseFormController.delete_requested` | Re-emits the user's delete intent with the current form payload. (The orchestrator does not use the payload, but the existing signal shape stays consistent across create/update/delete.) | delete-button click | `delete_requested(dict)` Qt signal |
| `gui.tab.TabController.delete_requested` | Tag the intent with this tab's `record_type` and re-emit. | `delete_requested(dict)` | `delete_requested(str, dict)` Qt signal |
| `gui.common.dialogs.confirm` | Modal Yes/No around an arbitrary title + body. Defaults to **No** so an accidental Enter on a focused dialog does not delete. Lives in `src/gui/common/dialogs.py` and is shared with `_on_clear_all`. | `parent: QWidget`, `title: str`, `body: str` | `bool` (True = user confirmed) |
| `gui.main_window.MainWindow._on_delete` | Orchestrator: resolve selection → confirm → build survivor list → save → swap state → reset form/selection → status. | `record_type: str`, `payload: dict` (ignored — delete keys off selection) | side-effects: in-memory state, file, form, table, status message |

### Data side — reused unchanged

| Module | Responsibility |
| --- | --- |
| `record.repository.save_records` | Atomic JSONL write — write `record.jsonl.tmp` then `os.replace`. |

No data-layer code changes are required.

---

## Edge Cases

| Case | Handling |
| --- | --- |
| User clicks **Delete** without first selecting a row | Status bar: `"Select a record to delete first."`; no dialog, no change. |
| Stored selection index is stale (out of range — e.g. a previous delete invalidated it but the user clicked Delete again on the same form) | Treated as no selection — same message. |
| User opens the confirmation dialog and clicks **No** (or closes the dialog) | Status bar: `"Delete cancelled."`; in-memory list and file are untouched. |
| User confirms deletion of the last record | `new_records` is `[]`; `save_records` writes an empty JSONL file; `load_records` would return `[]` on next launch. |
| User confirms deletion of a Flight (no own ID) | Works the same as Client/Airline — delete keys off the absolute index, not the ID. |
| Disk-write failure during `save_records` (`OSError` / `PermissionError`) | `self._records` is **not** reassigned; the previously selected row is still in memory and on disk. Status bar shows `"Save failed: …"`. |
| User had the form populated from an earlier row-click, then deletes that row | After a successful delete the form is re-populated with whatever record now sits at the same table-row position (or the last survivor if the deleted row was past the end). Consecutive Delete clicks therefore remove the next visible row without needing another click. If nothing of that type remains, the form is cleared and the per-type selection is `None`. |
| User has scrolled to a different page and the selection points to a record off-screen | Delete still operates on the absolute index, so the off-screen row is removed. After refresh the pager may move the user back a page if their page no longer has rows; this is handled by `paginate`'s existing clamp. |

---

## Error Handling Strategy

- **Where errors are detected**:
  - missing or stale selection is checked explicitly in `_on_delete` before any UI dialog.
  - user-declined confirmation is observed via the `bool` return of `confirm`.
  - persistence errors (`OSError`, including `PermissionError`) are raised by `save_records`.
- **How they are propagated**:
  - the data layer raises; it never logs, never returns error codes, never silently corrects.
  - the orchestrator (`MainWindow._on_delete`) is the only place that catches them.
- **How they are handled**:
  - missing selection → status bar prompt; function returns before touching anything.
  - declined confirmation → status bar `"Delete cancelled."`; function returns before touching anything.
  - persistence failure → status bar `"Save failed: <reason>"`. The new survivor list is built as a separate object and `self._records = new_records` is the **last** mutation, executed only after the save succeeds. This mirrors update's discipline: in-memory state never moves ahead of disk state.
- **What is NOT handled today** (known gaps):
  - There is no "undo last delete" — the survivor list is the new truth as soon as the save commits.
  - Concurrent edits from another process are not considered (single-user desktop tool).

---

## Why this shape

- **Delete keys off the selection, not the form payload.** The form's contents may have drifted away from the row the user actually clicked (they could have edited fields after selecting). Operating on `self._selected_index_by_type[record_type]` removes ambiguity: the deletion targets the row the user pointed at, full stop. The payload argument on the Qt slot is kept to match the create/update signal shape and is ignored on purpose.
- **Confirmation defaults to No.** Hitting Enter on a focused message box is too easy. The default button is `QMessageBox.No` so accidental dismissals do not delete data.
- **Confirmation lives behind a shared seam.** Tests should not pop a real dialog. `confirm` is imported by name in `gui.main_window`, so a one-line `monkeypatch.setattr(gui.main_window, "confirm", lambda *_: True)` substitutes both delete and clear-all dialogs without touching `QMessageBox` internals.
- **Build new list, then swap.** Mirrors the create-flow rollback and the update-flow swap: in-memory state is only mutated **after** persistence succeeds, so a disk failure can never leave the GUI and the file out of sync.
- **Re-select the same table-row position on success.** Most desktop apps let the user delete consecutive rows by clicking Delete repeatedly — the next row slots up into the deleted position and clicking Delete again removes it. We mirror that: the selection clamps to `min(deleted_position, len(survivors) - 1)` in the type-filtered list, and the form is populated with whatever record is now there. The deleted record's values do not stay on the form. If no survivors remain, the form is cleared and the selection is `None`.
- **No data-layer changes.** Delete is a removal at a known index plus a save. There is no business rule about *what* can be deleted (no foreign-key checks between Flight and Client/Airline today). Pushing logic into the data layer would be speculative; if a future story adds such a rule, this is where it lands.

---

## What happens when you click Delete

```
1. User clicks a row in the Client tab's RecordListView
       ↓ (Qt's QTableWidget.cellClicked signal — fires on every click,
          even re-clicking the same row index after a refresh)
2. RecordListController emits record_selected(row_index)
       ↓
3. TabController re-emits record_selected("Client", row_index)
       ↓
4. MainWindow._on_record_selected stores the absolute index and
   populates the form (shared with the update flow).
       ↓
5. User clicks [Delete] in ClientFormView
       ↓
6. BaseFormController emits delete_requested(payload)
       ↓
7. TabController re-emits delete_requested("Client", payload)
       ↓
8. MainWindow._on_delete("Client", payload):
       a. idx = self._selected_index_by_type.get("Client")
          → if None or out of range: status "Select a record to delete first.", return
       b. record = self._records[idx]
       c. if not confirm(self, "Confirm delete", f"Delete this Client record?\n\n{record}"):
              status "Delete cancelled.", return
       d. position = self._records_for_type("Client").index(record)  ← capture table-row position
       e. new_records = self._records[:idx] + self._records[idx + 1:]
       f. save_records(DATA_FILE_PATH, new_records)              ← atomic write
       g. self._records = new_records                            ← only AFTER save succeeds
       h. self._refresh_all_tables()
       i. self._reselect_after_delete("Client", position)        ← clamp to len-1 or None
       j. status bar: "Delete Client {...}"
```

If 8f raises `OSError`, the orchestrator catches it, shows `"Save failed: …"`, and skips 8g–8j — `self._records` is never reassigned and the selection is left exactly where it was, so the user can retry without re-clicking the row.

---

## Where to look when you want to change something

| To change | Edit |
| --- | --- |
| The text of the confirmation dialog | `src/gui/main_window.py` (`_on_delete`, the `body` literal) |
| The default button of the confirmation dialog | `src/gui/common/dialogs.py` (`confirm`) |
| Whether confirmation is required at all | `src/gui/main_window.py` (`_on_delete`, drop the `confirm(...)` call) |
| Behaviour after a successful delete (re-select same position, or clear) | `src/gui/main_window.py` (`_reselect_after_delete`) |
| How records are persisted (JSONL today) | `src/record/repository.py` (shared with create/update) |

---

## Suggested first read

Open `src/gui/main_window.py` and read `_on_delete` top to bottom — ten short steps and you have the whole feature. The confirmation dialog itself is a one-function file at `src/gui/common/dialogs.py`. Everything else (selection bookkeeping, table refresh, atomic save) is shared with create and update and is already documented in their design docs.