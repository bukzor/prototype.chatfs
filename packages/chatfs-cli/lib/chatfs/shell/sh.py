"""Minimal shell-tracing helper, adapted from ~/lib/pythonpath/bukzor/sh/io.py.

`xtrace` prints a copy-pasteable, `set -x`-style line to stderr for every
subprocess this codebase spawns. `log` is the general progress-message
counterpart other modules print through. Both are gated by `debug_enabled`
(`DEBUG=1` or higher) -- normal runs stay quiet; the trace is there for
when something needs debugging.

`run` traces, then runs a command to completion, always raising on
non-zero exit. Deliberately narrow signature (stdin/stdout handles);
grow it as needed. `pipe` is its two-stage counterpart, for a driver
whose job is to be a pipeline.

`caller_location` is the runtime stand-in for C's `__FILE__`/`__LINE__`
(Python has no preprocessor) -- for diagnostics that should point a
reader at the call site, not just describe it.
"""

import inspect
import os
import shlex
import subprocess
import sys
from collections.abc import Sequence
from typing import IO

_TEAL = "\033[36;1m"
_RESET = "\033[m"
PS4 = f"+ {_TEAL}${_RESET} "


def debug_enabled() -> bool:
    """True when $DEBUG is set to a positive integer."""
    return int(os.environ.get("DEBUG", "0") or "0") >= 1


def log(msg: str) -> None:
    """Print a progress message to stderr, gated by debug_enabled()."""
    if debug_enabled():
        print(msg, file=sys.stderr, flush=True)


def caller_location() -> str:
    """The calling line's `file:line`. `co_filename` (not `__file__`) is
    what makes this correct from any caller, in any module -- `__file__`
    would name wherever this function itself is defined."""
    frame = inspect.currentframe()
    assert frame is not None
    caller = frame.f_back
    assert caller is not None
    return f"{caller.f_code.co_filename}:{caller.f_lineno}"


def quote(cmd: Sequence[object]) -> str:
    """Escape a command to copy-pasteable shell form.

    >>> quote(("ls", "1 2", 3, "4"))
    "ls '1 2' 3 4"
    """
    return " ".join(shlex.quote(_stringify(arg)) for arg in cmd)


def xtrace(cmd: Sequence[object]) -> None:
    """Print a command to stderr in copy-pasteable, `set -x`-style form."""
    log(PS4 + quote(cmd))


def run(
    cmd: Sequence[object],
    *,
    stdin: IO[bytes] | int | None = None,
    stdout: IO[bytes] | int | None = None,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[bytes]:
    """Run a command to completion, tracing it first. Raises on non-zero exit.

    close_fds=False: the child inherits the whole fd table, matching plain
    Unix exec semantics -- Python's close_fds=True default silently drops
    any fd not explicitly listed in pass_fds.

    timeout unused by any production call site (2026-07-18); it exists so
    tests can bound a would-be deadlock instead of hanging the suite.
    """
    xtrace(cmd)
    return subprocess.run(
        [_stringify(arg) for arg in cmd],
        stdin=stdin,
        stdout=stdout,
        close_fds=False,
        check=True,
        timeout=timeout,
    )


def pipe(producer: Sequence[object], consumer: Sequence[object]) -> None:
    """Run `producer | consumer` to completion, tracing the whole line first.

    Raises on a non-zero exit from *either* stage -- `pipefail`, not the
    shell's last-stage-only default. `close_fds=False` for the same
    reason as `run`.
    """
    log(PS4 + f"{quote(producer)} | {quote(consumer)}")
    producer_argv = [_stringify(arg) for arg in producer]
    consumer_argv = [_stringify(arg) for arg in consumer]
    upstream = subprocess.Popen(producer_argv, stdout=subprocess.PIPE, close_fds=False)
    assert upstream.stdout is not None, upstream
    # The consumer dups the read end into its own fd 0; drop the parent's
    # handle once it has, so nothing here holds the pipe open.
    with upstream.stdout as read_end:
        downstream = subprocess.Popen(consumer_argv, stdin=read_end, close_fds=False)
    upstream_code = upstream.wait()
    downstream_code = downstream.wait()
    # Both are reaped before either is reported, and the producer is
    # reported first: when a browse fails, the splat's downstream
    # complaint about empty input is the symptom, not the cause.
    if upstream_code:
        raise subprocess.CalledProcessError(upstream_code, producer_argv)
    if downstream_code:
        raise subprocess.CalledProcessError(downstream_code, consumer_argv)


def _stringify(arg: object) -> str:
    if isinstance(arg, bytes):
        return arg.decode("US-ASCII")  # other bytes are ambiguous
    else:
        return str(arg)
