"""Minimal shell-tracing helper, adapted from ~/lib/pythonpath/bukzor/sh/io.py.

`xtrace` prints a copy-pasteable, `set -x`-style line to stderr for every
subprocess this codebase spawns. Unconditional for now (no `DEBUG`
env-var gate, no `quiet()`/`loud()` toggle like the source module has) --
add those back if a call site needs to suppress it.

`run` traces, then runs a command to completion, always raising on
non-zero exit. Deliberately narrow signature (stdin/stdout handles);
grow it as needed.
"""

import shlex
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import IO

_TEAL = "\033[36;1m"
_RESET = "\033[m"
PS4 = f"+ {_TEAL}${_RESET} "


def quote(cmd: Sequence[object]) -> str:
    """Escape a command to copy-pasteable shell form.

    >>> quote(("ls", "1 2", 3, "4"))
    "ls '1 2' 3 4"
    """
    return " ".join(shlex.quote(_stringify(arg)) for arg in cmd)


def xtrace(cmd: Sequence[object]) -> None:
    """Print a command to stderr in copy-pasteable, `set -x`-style form."""
    print(PS4 + quote(cmd), file=sys.stderr, flush=True)


def run(
    cmd: Sequence[object],
    *,
    stdin: IO[bytes] | int | None = None,
    stdout: IO[bytes] | int | None = None,
    cwd: Path | None = None,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[bytes]:
    """Run a command to completion, tracing it first. Raises on non-zero exit.

    close_fds=False: the child inherits the whole fd table, matching plain
    Unix exec semantics -- Python's close_fds=True default silently drops
    any fd not explicitly listed in pass_fds.

    cwd: needed by `python -m chatfs.…` delegation calls (`-m` puts the
    interpreter's cwd, not the invoking script's directory, at
    `sys.path[0]`), so the callee resolves the `chatfs` package
    regardless of the caller's own cwd.

    timeout unused by any production call site (2026-07-18); it exists so
    tests can bound a would-be deadlock instead of hanging the suite.
    """
    xtrace(cmd)
    return subprocess.run(
        [_stringify(arg) for arg in cmd],
        stdin=stdin,
        stdout=stdout,
        cwd=cwd,
        close_fds=False,
        check=True,
        timeout=timeout,
    )


def _stringify(arg: object) -> str:
    if isinstance(arg, bytes):
        return arg.decode("US-ASCII")  # other bytes are ambiguous
    else:
        return str(arg)
