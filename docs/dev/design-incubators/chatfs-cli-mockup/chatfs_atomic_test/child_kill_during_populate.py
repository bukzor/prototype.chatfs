"""Killed while the caller's populate body is still writing the scratch.

Prints "ready" once real bytes are on disk, then self-SIGSTOPs so the
parent can SIGKILL at an exact point -- no sleep-based race.
"""

import os
import signal
import sys
from pathlib import Path

import chatfs_atomic

dst = Path(sys.argv[1])
anchor = Path(sys.argv[2])

with chatfs_atomic.staged(dst, anchor=anchor) as tmp:
    _ = tmp.write_text("half-written")
    print("ready", flush=True)
    os.kill(os.getpid(), signal.SIGSTOP)
