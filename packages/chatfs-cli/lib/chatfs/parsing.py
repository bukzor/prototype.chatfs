"""Name the file a JSON decode error came from.

`JSONDecodeError` reports a line and column but not whose: by the time
it surfaces, the path is several frames up or gone. `parsing(path)`
wraps the read-and-parse of one file and notes the absolute path on
the error, so the traceback says which file to open.
"""

import json
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def parsing(path: Path) -> Generator[None]:
    """Note `path`, absolute, on any JSONDecodeError raised inside."""
    try:
        yield
    except json.JSONDecodeError as error:
        error.add_note(f"while parsing {path.absolute()}")
        raise
