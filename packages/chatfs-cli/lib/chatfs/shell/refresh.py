"""Refresh one provider: capture its index, then browse what's recent and stale.

Exception to chatfs/'s purity rule (see chatfs.shell's package docstring):
this runs the index and every conversation capture as subprocesses. The
rules it applies -- window, coverage, staleness -- are pure and live in
`chatfs.refresh`.
"""

import json
import subprocess
import sys
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

import typed_json
from typed_json import JsonObject
from chatfs.refresh import covers, cutoff_for, in_window, is_stale
from chatfs.shell import sh as chatfs_sh
from chatfs.shell.capture import captured_at


class IndexedChat(NamedTuple):
    """One placement record, with the two fields refresh decides on
    parsed out and the record itself kept whole -- what refresh writes
    back to stdout is what the index handed it, so a caller can pipe the
    refreshed subset onward exactly as it would the full index."""

    chat_dir: Path
    updated: datetime | None
    record: JsonObject


def parse_index(stdout: bytes) -> list[IndexedChat]:
    """Read an index driver's placement-record stream."""
    chats: list[IndexedChat] = []
    for line in stdout.decode().splitlines():
        record = typed_json.loads(line)
        assert typed_json.is_json_object(record), record
        chat_dir = record["chat_dir"]
        assert isinstance(chat_dir, str), record
        updated = record["updated"]
        assert updated is None or isinstance(updated, str), record
        chats.append(
            IndexedChat(
                Path(chat_dir),
                datetime.fromisoformat(updated) if updated else None,
                record,
            )
        )
    return chats


def capture_index(provider: str, cache: Path) -> list[IndexedChat]:
    """Run the provider's index driver and read back what it placed.

    Browses: a window opens and waits for the human, same as any other
    capture in this codebase.
    """
    done = chatfs_sh.run(
        [sys.executable, "-m", f"chatfs.provider.{provider}.index", "--cache", cache],
        stdout=subprocess.PIPE,
    )
    return parse_index(done.stdout)


def browse_chat(provider: str, chat_dir: Path) -> None:
    """Capture one conversation by its chat-dir address."""
    _ = chatfs_sh.run(
        [
            sys.executable,
            "-m",
            f"chatfs.provider.{provider}.conversation.path_browse",
            chat_dir,
        ],
    )


def report_undated(chats: Sequence[IndexedChat]) -> None:
    """Say how many records the provider sent without a timestamp.

    Unconditional, not debug-gated: those chats are skipped whatever
    state they're in, and an operator who is told nothing has no way to
    tell a quiet refresh from a blind one.
    """
    undated = sum(1 for chat in chats if chat.updated is None)
    if undated:
        print(
            f"{undated} record(s) carried no timestamp and were skipped",
            file=sys.stderr,
        )


def refresh_provider(provider: str, cache: Path, days: int, now: datetime) -> int:
    """Bring one provider's cache up to date over the last `days`, and
    return the exit status: 3 when the index didn't reach past the
    window, 1 when some capture failed, 0 otherwise.

    stdout is one placement record per conversation actually refreshed.
    Skips are debug-gated -- on a large account they are the bulk of the
    run, and the point of refresh is that they cost nothing.

    Coverage is checked before the first browse deliberately: an index
    that stopped inside the window buys an incomplete set, and finding
    that out afterward would have spent the operator's whole attention
    budget first.
    """
    cutoff = cutoff_for(days, now)
    chats = capture_index(provider, cache)

    if not covers([chat.updated for chat in chats], cutoff):
        print(
            f"{provider}: the captured index reaches no further back than "
            + f"{cutoff.date().isoformat()}, so a {days}-day refresh cannot be "
            + "complete. Re-run with the sidebar scrolled back past that date.",
            file=sys.stderr,
        )
        return 3

    report_undated(chats)

    failures = 0
    for chat in chats:
        if not in_window(chat.updated, cutoff):
            chatfs_sh.log(f"skipping {chat.chat_dir}: outside the {days}-day window")
            continue
        assert chat.updated is not None, chat
        if not is_stale(chat.updated, captured_at(chat.chat_dir)):
            chatfs_sh.log(f"skipping {chat.chat_dir}: captured since its last change")
            continue
        try:
            browse_chat(provider, chat.chat_dir)
        except subprocess.CalledProcessError as error:
            failures += 1
            print(
                f"{provider}: capture failed for {chat.chat_dir} "
                + f"(exit {error.returncode})",
                file=sys.stderr,
            )
        else:
            print(json.dumps(chat.record))

    return 1 if failures else 0
