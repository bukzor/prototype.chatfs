"""Stage-and-promote filesystem updates: readers never see partial state.

Design sketch -- imported nowhere yet; landing tracked by
`.claude/todo.kb/2026-07-13-000-Atomic-chat-dir-regeneration-...`.
Normative design: `design.kb/040-design.kb/chat-as-directory.md` and
`deterministic-regeneration.md` (their [!TODO] blocks).

A destination (file, directory, or symlink) is updated by building its
complete replacement at a hidden sibling scratch path, then renaming it
into place -- rename(2) is the atomicity primitive, and a sibling is on
the same filesystem by construction. The old version is destroyed only
after (or atomically with) its replacement's installation. A failed
attempt -- exception or crash alike -- leaves its bytes on disk at a
`.fail` sibling for inspection instead of vanishing.

Sibling naming for a destination `name`: `.name.tmp` (scratch),
`.name.old` (two-rename intermediate), `.name.fail` (preserved failed
attempt). Dot-prefixed so in-flight artifacts stay out of default `ls`
on the served surface.

Locking contract: `staged` takes the write lock itself, over `anchor` --
any agreed-per-destination directory that itself never gets renamed;
chatfs uses `.data/$UUID/`. `chatfs_locks` is process-tree-reentrant, so
this is safe to nest: a caller that must *span* multiple staged
promotions as one transition (capture()'s two files, place_meta's
promote-plus-symlink-sweep) wraps them in its own outer
`chatfs_locks.write_locked(anchor)` -- each inner `staged` call then
borrows that lock instead of re-acquiring it, so it stays held for the
whole span. A single `staged` call needs no such wrapping. Cooperating
readers wrap reads in `chatfs_locks.read_locked` to observe a
multi-step update as a single transition; non-cooperating readers (a
human mid-`ls`) still see each destination only old-complete or
new-complete, never partial. Crash safety needs no lock cleanup: the
kernel releases flocks with the process.

Intended shape of chatfs regeneration:

    with staged(chat_dir, anchor=data_dir) as tmp:  # .data/$UUID/
        tmp.mkdir()
        (tmp / ".data").symlink_to(f"../../.data/{uuid}")
        splat(conversation, out=tmp)         # tmp/messages, tmp/conversations
        render(tmp, out=tmp / "chat.md")

Out of scope by decision: fsync/power-loss durability (the requirement's
verification is process-kill) and cross-filesystem staging.
"""

import ctypes
import errno
import os
import shutil
import stat
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import cast

import chatfs_locks

_AT_FDCWD = -100  # linux/fcntl.h
_RENAME_EXCHANGE = 2  # linux/fs.h


@contextmanager
def staged(dst: Path, *, anchor: Path) -> Generator[Path]:
    """Yield a scratch path; what the caller builds there is atomically
    promoted to `dst` on success.

    Takes `anchor`'s write lock for the duration (see module docstring:
    "Locking contract"); reentrant, so nesting inside a caller-held lock
    on the same anchor just borrows it.

    The scratch is reserved, not created: materialize it as a file,
    directory, or symlink -- or rename an already-built tree onto it.
    On exception the scratch rotates to `.fail` and `dst` is untouched;
    on success a stale `.fail` is cleared (superseded evidence). Entry
    heals whatever a previously-killed run left behind.
    """
    with chatfs_locks.write_locked(anchor):
        recover(dst)
        tmp = _sibling(dst, "tmp")
        try:
            yield tmp
        except BaseException:
            if os.path.lexists(tmp):
                _rotate_to_fail(tmp, dst)
            raise
        assert os.path.lexists(tmp), tmp
        _promote(tmp, dst)
        _remove(_sibling(dst, "fail"))


def recover(dst: Path) -> None:
    """Return `dst`'s neighborhood to the ready state; idempotent.

    Each way a previous run can have been killed leaves a distinct
    fingerprint:

    - scratch present: died mid-populate; preserve as `.fail` (latest
      wins), the same end state an exception produces.
    - `dst` absent, `.old` present: died between `_swap_via_old`'s two
      renames; the old version is the only complete one -- restore it.
    - `dst` and `.old` both present: died after the swap, before
      cleanup; the old version is superseded -- discard it.
    """
    tmp = _sibling(dst, "tmp")
    if os.path.lexists(tmp):
        _rotate_to_fail(tmp, dst)
    old = _sibling(dst, "old")
    if os.path.lexists(old):
        if os.path.lexists(dst):
            _remove(old)
        else:
            os.rename(old, dst)


def _promote(src: Path, dst: Path) -> None:
    """Atomically install `src` at `dst`; `src` ceases to exist.

    Any observer sees the old complete `dst` or the new one -- never
    absence, never a mixture. Internal to `staged`, which holds the
    write lock for the call.
    """
    if not os.path.lexists(dst):
        os.rename(src, dst)
    elif not _is_real_dir(src) and not _is_real_dir(dst):
        os.replace(src, dst)  # files and symlinks: single-syscall swap
    elif _is_real_dir(src) and _is_real_dir(dst) and _exchange(src, dst):
        shutil.rmtree(src)  # src now holds the displaced old version
    else:
        # dir-over-dir without exchange support, or a type change:
        # rename(2) won't clobber a non-empty dir, so go via .old.
        _swap_via_old(src, dst)


def _swap_via_old(src: Path, dst: Path) -> None:
    """Two renames with a syscall-width gap; recover() heals a kill between."""
    old = _sibling(dst, "old")
    _remove(old)
    os.rename(dst, old)
    os.rename(src, dst)
    _remove(old)


def _exchange(a: Path, b: Path) -> bool:
    """renameat2(RENAME_EXCHANGE): swap two paths in one syscall.

    False when unsupported (non-Linux libc, kernel < 3.15, or a
    filesystem without exchange); the caller falls back to
    `_swap_via_old`.
    """
    try:
        renameat2 = ctypes.CDLL(None, use_errno=True).renameat2
    except AttributeError:
        return False
    ret = cast(
        "int",
        renameat2(_AT_FDCWD, os.fsencode(a), _AT_FDCWD, os.fsencode(b), _RENAME_EXCHANGE),
    )
    if ret == 0:
        return True
    err = ctypes.get_errno()
    if err in {errno.EINVAL, errno.ENOSYS, errno.ENOTSUP}:
        return False
    raise OSError(err, os.strerror(err), str(a), None, str(b))


def _rotate_to_fail(tmp: Path, dst: Path) -> None:
    fail = _sibling(dst, "fail")
    _remove(fail)  # latest failure wins
    os.rename(tmp, fail)


def _sibling(dst: Path, kind: str) -> Path:
    """Hidden in-flight sibling: `.{name}.{kind}`, same filesystem as `dst`."""
    return dst.parent / f".{dst.name}.{kind}"


def _is_real_dir(path: Path) -> bool:
    """A directory itself, not a symlink to one: rename semantics differ."""
    return stat.S_ISDIR(os.lstat(path).st_mode)


def _remove(path: Path) -> None:
    """Remove an in-flight artifact of any type; absent is fine."""
    if not os.path.lexists(path):
        return
    if _is_real_dir(path):
        shutil.rmtree(path)
    else:
        os.unlink(path)
