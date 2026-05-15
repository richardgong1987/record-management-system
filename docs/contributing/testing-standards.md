# Unit Testing Standards

Practical conventions the team follows for every unit test under [tests/unit/](../../tests/unit/). The CSCK541 brief asks for unit tests per module; these standards keep the suite simple and readable as it grows.

> The test suite is split by category: `tests/unit/` (where every current test lives), with `tests/integration/` and `tests/e2e/` reserved for the future integration and end-to-end suites. The conventions below apply to **unit tests**; integration/e2e tests will get their own standards once those suites land.

## Useful links

- [Developer workflow](developer-workflow.md)
- [Git commit conventions](commit-conventions.md)
- pytest docs on parametrize: <https://docs.pytest.org/en/stable/how-to/parametrize.html>

## 1. Default to `@pytest.mark.parametrize`

Whenever two or more tests share the same body and only differ in inputs or expected outputs, write **one** parametrized test instead of multiple copy-pasted functions.

This is our primary readability rule for tests. It:

- Keeps each "behaviour under test" in one place — adding a new case is one row in a table, not a new function.
- Makes the suite visually scannable — the table reads like a spec.
- Catches more cases for the same effort, because adding the next variant is cheap.
- Surfaces the contract: what changes between cases is exactly what the test is varying.

### Bad — three copy-pasted tests

```python
def test_check_positive_integers_rejects_zero():
    with pytest.raises(RecordValidationError, match="ID must be greater than zero"):
        check_positive_integers({"Type": "Client", "ID": 0})


def test_check_positive_integers_rejects_negative():
    with pytest.raises(RecordValidationError, match="ID must be greater than zero"):
        check_positive_integers({"Type": "Client", "ID": -1})


def test_check_positive_integers_rejects_flight_zero_airline_id():
    with pytest.raises(RecordValidationError, match="Airline_ID must be greater than zero"):
        check_positive_integers({"Type": "Flight", "Client_ID": 1, "Airline_ID": 0})
```

### Good — one parametrized test

```python
@pytest.mark.parametrize(
    "record,expected_field",
    [
        pytest.param({"Type": "Client", "ID": 0},  "ID",          id="client-id-zero"),
        pytest.param({"Type": "Client", "ID": -1}, "ID",          id="client-id-negative"),
        pytest.param(
            {"Type": "Flight", "Client_ID": 1, "Airline_ID": 0},
            "Airline_ID",
            id="flight-airline-id-zero",
        ),
    ],
)
def test_check_positive_integers_rejects_non_positive(record, expected_field):
    with pytest.raises(
        RecordValidationError,
        match=f"{expected_field} must be greater than zero",
    ):
        check_positive_integers(record)
```

## 2. House style for `parametrize`

A few conventions that keep the tables readable:

- **Always wrap each row in `pytest.param(..., id="kebab-case")`.** Named IDs read in CI logs and `pytest -k` filters far better than the auto-generated ones (`record0`, `record1`).
- **Hoist shared fixtures to module-level constants** (`CLIENT_RECORD = {...}`) so the table doesn't drown in payload literals.
- **Keep one parametrized test per behaviour.** If two cases need different assertions, they are different behaviours — split them.
- **Order the columns the way the case reads aloud:** `(input, expected_output)`, or `(setup, action, expected)`.
- **Name parameters after their role**, not their type: `record`, `expected_field`, `update_payload` — not `data`, `value`, `x`.

## 3. When separate tests are OK

Parametrize is the default, not a mandate. Keep tests separate when:

- The cases need genuinely **different setup or fixtures** (e.g., one builds a `MainWindow`, another patches `confirm` first).
- The cases need genuinely **different assertions** (one asserts on records, another on the status bar text).
- The test is a **multi-step end-to-end narrative** — clicking, asserting state, clicking again — where collapsing into a table would obscure the story.
- There is **only one case** and no near-future variants are likely.

If you find yourself parametrizing over a single case "just in case", don't. Add the parametrize when the second case actually shows up.

## 4. Patterns we use repeatedly

These are the parametrize shapes that come up most often in this repo — copy them rather than reinventing.

### Multiple invalid inputs, same exception

```python
@pytest.mark.parametrize(
    "id_value",
    ["abc", "1.5", "1 2", "0x10", " "],
    ids=["letters", "float-string", "spaces-between", "hex", "single-space"],
)
def test_non_integer_id_reports_whole_number_message(id_value):
    with pytest.raises(RecordValidationError, match="ID must be a whole number"):
        create_record("Client", _client(ID=id_value))
```

### Same behaviour across exception subclasses

`OSError` and `PermissionError` (an `OSError` subclass) must both be caught by the orchestrator. Parametrize over the exception instance:

```python
@pytest.mark.parametrize(
    "exc",
    [
        pytest.param(OSError("Disk full"),       id="disk-full-oserror"),
        pytest.param(PermissionError("read-only"), id="permission-error"),
    ],
)
def test_save_failure_rolls_back_in_memory_append(main_window, monkeypatch, exc):
    ...
```

### Same behaviour across record types

```python
@pytest.mark.parametrize(
    "record_type,seed_payload,update_payload,expected_field,expected_value",
    [
        pytest.param("Airline", _airline_payload(...), _airline_payload(...),
                     "Company Name", "Acme Aviation", id="airline"),
        pytest.param("Flight",  _flight_payload(),    _flight_payload(date="..."),
                     "Date",         "2026-07-04T12:00:00", id="flight-no-own-id"),
    ],
)
def test_update_works_for_record_type(main_window, ...):
    ...
```

### Multiple "produces empty" setups

When several setups all yield the same "should be empty" assertion, pass a setup callable as the parameter:

```python
@pytest.mark.parametrize(
    "prepare_file",
    [
        pytest.param(lambda path: None, id="missing-file"),
        pytest.param(lambda path: path.write_text("", encoding="utf-8"), id="empty-file"),
    ],
)
def test_load_records_returns_empty_list(tmp_path, prepare_file):
    path = tmp_path / "records.jsonl"
    prepare_file(path)
    assert load_records(path) == []
```

## 5. Other test-writing rules

These predate the parametrize rule and still apply.

- **One module per `src/` package.** A `src/foo/bar.py` module is tested by `tests/unit/foo/test_bar.py`. The brief requires unit tests per module — match the layout so coverage gaps are visible.
- **Use `tmp_path` for anything that touches the filesystem.** Never write to the real `src/data/record.jsonl` from a test.
- **Use `monkeypatch` for module-level constants and dependencies.** For the GUI, that means patching `DATA_FILE_PATH` and `confirm` on the `gui.main_window` module before instantiating `MainWindow`.
- **Pin exception types tightly.** `pytest.raises(Exception)` is too broad — it masks regressions. Prefer the specific class (e.g. `pytest.raises(jsonlines.InvalidLineError)`) and add `match="..."` when the message is part of the contract.
- **Test behaviour, not implementation.** Assert observable outcomes (return values, file contents, status-bar text), not internal call counts or private attributes.

## 6. Quick checklist

Before opening a PR that adds or changes tests:

- [ ] Any two test functions with the same body have been collapsed into one parametrized test.
- [ ] Each parametrized case has a `pytest.param(..., id="...")` ID.
- [ ] Filesystem-touching tests use `tmp_path`, not the real data file.
- [ ] `pytest.raises(...)` names a specific exception class, not bare `Exception`.
- [ ] `python -m pytest` runs green locally.
