"""Foreseen failures, reported as a message rather than a traceback.

A traceback says the code is wrong, and points at where. A `UserError`
says the code did its job and found something only the user can fix --
scroll further, capture another way -- so its message is the whole
report and a traceback would only bury it.
"""

import functools
import sys
from collections.abc import Callable


class UserError(Exception):
    """A foreseen failure: `str()` is what the user reads (empty means
    nothing further to say), `status` the command's exit status."""

    def __init__(self, message: str = "", status: int = 1):
        super().__init__(message)
        self.status: int = status


def reports_user_errors(main: Callable[[], None]) -> Callable[[], None]:
    """Wrap a command's `main` so a UserError exits with its status,
    printing its message (if any) to stderr and no traceback. Every other
    exception still surfaces with its traceback."""

    @functools.wraps(main)
    def wrapper() -> None:
        try:
            main()
        except UserError as error:
            if str(error):
                print(error, file=sys.stderr)
            sys.exit(error.status)

    return wrapper
