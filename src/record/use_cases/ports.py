from typing import Callable

# Persistence port. Implemented by the View as a closure over the data file
# path; tests pass a stub that raises ``OSError`` to exercise save-failure
# branches. The use case treats the call as fire-and-forget on success.
Save = Callable[[list[dict]], None]

# Confirmation port. ``(title, body) -> bool``. ``True`` means the user
# confirmed; ``False`` means they dismissed the dialog and the use case
# should return ``Cancelled``. Tests pass a stub returning ``True``/``False``.
Confirm = Callable[[str, str], bool]
