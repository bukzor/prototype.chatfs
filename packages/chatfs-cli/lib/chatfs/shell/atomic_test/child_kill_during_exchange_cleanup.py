"""Killed mid-`shutil.rmtree` cleanup that follows a successful
RENAME_EXCHANGE promote -- exercises the real exchange path (not the
fallback), proving dst is already fully-new before the crash, regardless
of what happens to the displaced old copy afterward.
"""

import os
import signal
import sys
from pathlib import Path

from chatfs.shell import atomic as chatfs_atomic

dst = Path(sys.argv[1])
anchor = Path(sys.argv[2])

real_unlink = os.unlink
calls = 0


def spy_unlink(path: str | os.PathLike[str], *, dir_fd: int | None = None) -> None:
    global calls
    calls += 1
    real_unlink(path, dir_fd=dir_fd)
    if calls == 1:
        print("ready", flush=True)
        os.kill(os.getpid(), signal.SIGSTOP)


os.unlink = spy_unlink

with chatfs_atomic.staged(dst, anchor=anchor) as tmp:
    tmp.mkdir()
    _ = (tmp / "new_file").write_text("new")
