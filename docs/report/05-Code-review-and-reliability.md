## Code Review and Reliability

During development, internal code review identified two technical concerns, which were resolved before submission.

The first concerned file save reliability. The `save_records` function in `src/record/repository.py` writes records to a temporary file and calls `os.replace`, but originally the callers mutated the in-memory record list before persisting, so a filesystem error left the application state inconsistent with the disk file. The fix lives in the use case layer under `src/record/use_cases/` (`create.py`, `update.py`, `delete.py`, `clear_all.py`): each use case now builds a fresh `new_records` list, calls the save port inside a `try/except OSError`, and only returns the new list to `MainWindow` once persistence has succeeded. On failure the use case returns an `Err`.

The second concerned validation order in `src/record/service.py`. The `create_record` function originally validated fields before converting string inputs to their correct types. This was corrected so type coercion runs first, ensuring validation operates on properly typed data. A `test_service.py` hotfix test confirms this.
