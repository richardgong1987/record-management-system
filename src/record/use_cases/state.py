from dataclasses import dataclass


@dataclass(frozen=True)
class State:
    # Snapshot the View hands to a use case. ``records`` is the full list
    # (all record types); ``selected`` is the dict currently selected on
    # the tab being operated on, or ``None`` if no row is highlighted.
    records: list[dict]
    selected: dict | None
