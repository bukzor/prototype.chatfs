"""Killed after both `_swap_via_old` renames commit (dst already holds the
new version) but before the final `.old` removal -- forces the
RENAME_EXCHANGE-unsupported fallback to reach that path.
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
    if calls == 2:
        print("ready", flush=True)
        os.kill(os.getpid(), signal.SIGSTOP)


os.rename = spy_rename

with chatfs_atomic.staged(dst, anchor=anchor) as tmp:
    tmp.mkdir()
    _ = (tmp / "new_file").write_text("new")
