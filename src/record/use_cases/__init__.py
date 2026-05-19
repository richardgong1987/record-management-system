"""Application / Use Case layer for record operations.

Each use case takes a ``State`` snapshot and returns a ``Result``. Side
effects (persistence, confirmation prompts) flow in through constructor-
injected ports, so the use cases hold no module-level state and have no
``from gui.*`` imports.
"""

from record.use_cases.clear_all import ClearAllRecords
from record.use_cases.create import CreateRecord
from record.use_cases.delete import DeleteRecord
from record.use_cases.result import Cancelled, Err, Ok, Result
from record.use_cases.state import State
from record.use_cases.update import UpdateRecord

__all__ = [
    "Cancelled",
    "ClearAllRecords",
    "CreateRecord",
    "DeleteRecord",
    "Err",
    "Ok",
    "Result",
    "State",
    "UpdateRecord",
]
