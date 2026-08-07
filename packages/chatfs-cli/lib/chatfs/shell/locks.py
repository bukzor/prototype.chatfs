"""Process-tree-reentrant advisory locks over per-chat anchor dirs.

The lock table lives in two synchronized forms: `registry` (in-process
truth) and the `__CHATFS_LOCKS` environment variable (`"11:r 22:w"` --
its serialization, rewritten eagerly on every acquire/release so no
spawn path, wrapped or not, ever inherits a stale table). Lock fds are
opened inheritable (no O_CLOEXEC), so they survive fork and exec through
any close_fds=False spawn -- chatfs.shell.sh.run in production, this
module's own `run()` (explicit pass_fds) in tests; a child re-entering a
held anchor finds the inherited fd by identity probe (st_dev, st_ino) and
borrows it instead of self-deadlocking on a fresh open-file-description.

Borrowed vs owned is the load-bearing bit: a no-op acquisition is a
no-op release. Only the scope that created the OFD closes it; a borrow
must not close the fd nor drop the table entry, or this process's own
children lose the lock from *their* table.

Mode logic never calls flock on a held OFD -- a second flock() call
converts (downgrades!) the existing lock:
  held w, want r or w  -> borrow, no syscall
  held r, want r       -> borrow, no syscall
  held r, want w       -> assert: no upgrade (the kernel upgrades by
                          release-then-reacquire, silently breaking the
                          read view); declare write_locked at the top.

Scope: locks belong to the process tree -- threads within a process are
inside the transaction by definition. A spawner that bypasses `run()`
(bare exec, multiprocessing spawn) drops fds but keeps env: the child
warns (EBADF at seed), acquires fresh, and at worst blocks visibly
against its own ancestor -- never silently.

Anchors are directories that never get renamed; chatfs uses
`.data/$UUID/`. See chatfs.shell.atomic for the staged-promotion side.
"""

import fcntl
import os
import stat
import subprocess
import sys
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Literal, NamedTuple

_ENV = "__CHATFS_LOCKS"

Mode = Literal["r", "w"]
_FLOCK_OP: dict[Mode, int] = {"r": fcntl.LOCK_SH, "w": fcntl.LOCK_EX}


class Lock(NamedTuple):
    fd: int
    mode: Mode
    owned: bool  # False: inherited; never close, never unregister


registry: dict[tuple[int, int], Lock] = {}  # (st_dev, st_ino) of the anchor
_seeded = False


@contextmanager
def read_locked(anchor: Path) -> Generator[None]:
    """Hold (or borrow) a shared lock on the anchor dir."""
    yield from _locked(anchor, "r")


@contextmanager
def write_locked(anchor: Path) -> Generator[None]:
    """Hold (or borrow) an exclusive lock on the anchor dir."""
    yield from _locked(anchor, "w")


def run(
    argv: Sequence[str | Path],
    *,
    capture_output: bool = False,
    timeout: float | None = None,
    env: Mapping[str, str] | None = None,
    check: bool = False,
) -> subprocess.CompletedProcess[bytes]:
    """subprocess.run carrying the lock table's fds to the child via pass_fds.

    Test/orchestration use -- production call sites spawn through
    chatfs.shell.sh.run instead, which inherits the whole fd table (lock
    fds included) rather than naming a curated list. Deliberately narrow
    signature (bytes-only); grow parameters as call sites need them.
    """
    _seed()
    return subprocess.run(
        argv,
        capture_output=capture_output,
        timeout=timeout,
        env=env,
        check=check,
        pass_fds=tuple(lock.fd for lock in registry.values()),
    )


def _locked(anchor: Path, mode: Mode) -> Generator[None]:
    _seed()
    key = _key(anchor)
    held = registry.get(key)
    if held is not None:
        assert not (mode == "w" and held.mode == "r"), (
            f"write requested under read lock on {anchor}: no upgrade -- "
            "the kernel upgrades by release-then-reacquire; "
            "declare write_locked at the top"
        )
        yield  # borrow: no flock call (it would convert the held lock)
        return
    fd = os.open(anchor, os.O_RDONLY | os.O_DIRECTORY)
    os.set_inheritable(fd, True)  # survive exec via chatfs.shell.sh.run's close_fds=False
    try:
        fcntl.flock(fd, _FLOCK_OP[mode])
        registry[key] = Lock(fd, mode, owned=True)
        _sync_env()
        try:
            yield
        finally:
            del registry[key]
            _sync_env()
    finally:
        os.close(fd)  # releases the flock


def _key(anchor: Path) -> tuple[int, int]:
    st = os.stat(anchor)
    return (st.st_dev, st.st_ino)


def _sync_env() -> None:
    """Registry mutation and env rewrite are one transaction."""
    if registry:
        os.environ[_ENV] = " ".join(f"{lock.fd}:{lock.mode}" for lock in registry.values())
    else:
        _ = os.environ.pop(_ENV, None)


def _seed() -> None:
    """Adopt inherited lock fds (once) from the env table, as borrowed.

    Identity comes from the fd itself (fstat), not from the requested
    anchor, so the whole table seeds in one pass. S_ISDIR filters fd-
    number collisions after an exec (anchors are always dirs); EBADF
    warns instead of dropping silently -- it means "spawned without fd
    inheritance", and that's the difference between a diagnosable hang
    and a mystery one.
    """
    global _seeded
    if _seeded:
        return
    _seeded = True
    for entry in os.environ.get(_ENV, "").split():
        fd_s, _, mode = entry.partition(":")
        assert mode in ("r", "w"), entry
        fd = int(fd_s)
        try:
            st = os.fstat(fd)
        except OSError:
            print(
                f"chatfs.shell.locks:{_ENV} lists fd {fd}:{mode} but it is not open; spawned without lock-fd inheritance?",
                file=sys.stderr,
            )
            continue
        if not stat.S_ISDIR(st.st_mode):
            print(
                f"chatfs.shell.locks:{_ENV} fd {fd}:{mode} is not a directory; ignoring",
                file=sys.stderr,
            )
            continue
        registry[(st.st_dev, st.st_ino)] = Lock(fd, mode, owned=False)
    _sync_env()  # drop stale entries from the serialized form too
