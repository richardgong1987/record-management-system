from dataclasses import dataclass


@dataclass(frozen=True)
class Ok:
    # Successful outcome. ``new_records`` is the full post-op list (the View
    # swaps ``MainWindow._records`` to this). ``new_selection`` is the dict
    # the operating tab should point at next (``None`` clears the slot).
    # ``repaint_form`` asks the View to re-populate / clear the form widget
    # for the operating tab — true after Delete / Clear-All, false after
    # Create / Update where the form already reflects the desired state.
    new_records: list[dict]
    new_selection: dict | None
    message: str
    repaint_form: bool = False


@dataclass(frozen=True)
class Err:
    # Validation or persistence failure. The View shows ``message`` in the
    # status bar and leaves ``_records`` / ``_selected_record_by_type``
    # untouched.
    message: str


@dataclass(frozen=True)
class Cancelled:
    # User dismissed a confirmation dialog. Same View behaviour as ``Err``
    # but kept distinct so cancellation never looks like an error.
    message: str


Result = Ok | Err | Cancelled
