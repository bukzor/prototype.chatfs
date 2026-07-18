"""Killed in the syscall-width gap inside `_swap_via_old`, between its two
renames -- forces the RENAME_EXCHANGE-unsupported fallback so that gap is
reachable at all. Pauses after the first rename (dst -> .old) commits,
before the second (.tmp -> dst) runs.
"""

import os
import signal
import sys
from pathlib import Path

import chatfs_atomic

dst = Path(sys.argv[1])
anchor = Path(sys.argv[2])

chatfs_atomic._exchange = lambda a, b: False  # pyright: ignore[reportPrivateUsage]

real_rename = os.rename
calls = 0


def spy_rename(src: str | os.PathLike[str], target: str | os.PathLike[str]) -> None:
    global calls
    calls += 1
    real_rename(src, target)
    if calls == 1:
        print("ready", flush=True)
        os.kill(os.getpid(), signal.SIGSTOP)


os.rename = spy_rename

with chatfs_atomic.staged(dst, anchor=anchor) as tmp:
    tmp.mkdir()
    _ = (tmp / "new_file").write_text("new")
