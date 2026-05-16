## Code Review and Reliability

During development, internal code review identified two technical concerns, both logged in GitHub Issue 30 and resolved before submission.

The first concerned file save reliability. The `save_records` function in `src/record/repository.py` wrote records to a temporary file and called `os.replace` without error handling. If a filesystem error occurred after a new record had been appended to the in-memory list, the application state could become inconsistent and the record would not persist after restart. The fix wraps save operations in a `try/except OSError` block, rolling back the in-memory change if saving fails and displaying an error message to the user.

The second concerned validation order in `src/record/service.py`. The `create_record` function originally validated fields before converting string inputs to their correct types. This was corrected so type coercion runs first, ensuring validation operates on properly typed data. A dedicated hotfix test in `test_service.py` confirms the correction works as expected.
