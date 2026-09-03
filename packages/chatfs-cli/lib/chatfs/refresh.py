#!/usr/bin/env python3
"""Which conversations a refresh is worth opening, and the fan-out over providers.

Usage:
    chatfs-refresh [--cache <dir>] <days>

Runs every provider's own `refresh` in turn, forwarding argv untouched.
A provider that fails does not cost the others their refresh: each
outcome is summarized on stderr, and the exit status is non-zero when
any of them failed.

The selection rules here are pure; `chatfs.shell.refresh` applies them
to a captured index and does the browsing.
"""

from collections.abc import Iterable, Sequence
from datetime import datetime, timedelta


def cutoff_for(days: int, now: datetime) -> datetime:
    """The oldest `updated` timestamp a chat can carry and still count as
    recent."""
    return now - timedelta(days=days)


def in_window(updated: datetime | None, cutoff: datetime) -> bool:
    """Whether the provider says this chat changed inside the window.

    An unknown timestamp is not recent. It is no evidence of recency,
    and reading it the other way would open a window for every chat
    whose payload omits the field -- the one cost an attended tool
    cannot absorb.
    """
    return updated is not None and updated >= cutoff


def covers(updateds: Iterable[datetime | None], cutoff: datetime) -> bool:
    """Whether the captured index reached past the window's far edge.

    One indexed chat older than the cutoff is the proof: nothing scrolls
    the sidebar, so an index that stops inside the window is a partial
    answer that looks like a complete one.
    """
    return any(u is not None and u < cutoff for u in updateds)


def is_stale(updated: datetime, captured: datetime | None) -> bool:
    """Whether the provider changed this chat since the local capture.

    `updated` is narrower than the record's own field on purpose: the
    window filter has already dropped the unknown-timestamp chats before
    staleness is asked.
    """
    return captured is None or captured < updated


def day_count(rest: Sequence[str]) -> int | None:
    """The window size from a leaf's remaining positional args, or None
    when they don't spell exactly one positive integer."""
    if len(rest) != 1 or not rest[0].isdigit():
        return None
    days = int(rest[0])
    return days if days > 0 else None


def main() -> None:
    import subprocess
    import sys

    from chatfs.provider.registry import PROVIDERS
    from chatfs.shell import sh as chatfs_sh

    failed: list[str] = []
    for provider in sorted(PROVIDERS):
        module = f"chatfs.provider.{provider}.refresh"
        try:
            _ = chatfs_sh.run([sys.executable, "-m", module, *sys.argv[1:]])
        except subprocess.CalledProcessError as error:
            failed.append(provider)
            print(f"{provider}: FAILED (exit {error.returncode})", file=sys.stderr)
        else:
            print(f"{provider}: ok", file=sys.stderr)

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
