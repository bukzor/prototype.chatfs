"""Capture: browse + pluck, landing exhaust into `.data/$UUID/`.

Exception to chatfs/'s purity rule (see chatfs.shell's package docstring):
every function here does real I/O -- subprocess, filesystem, or both.
"""

import json
import sys
from collections.abc import Callable, Iterable, Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

from typed_json import JsonValue
from chatfs.layout import data_dir_of
from chatfs.shell import atomic as chatfs_atomic
from chatfs.shell import locks as chatfs_locks
from chatfs.shell import sh as chatfs_sh


def run_module(module: str, src: Path, dst: Path) -> None:
    """Run `python -m module` as an external filter: read src, write its stdout to dst.

    Shared low-level primitive behind pipeline stages that still shell
    out to a separate process rather than run in-process -- the
    `conversation.json.d/raw.*` -> `conversation.json` stages, AI
    Studio's massage and chatgpt's assemble. `-m`, not a direct script
    path, so the callee resolves `chatfs.*` imports the same way every
    other subprocess delegation in this codebase does: via the installed
    package, from any cwd. Kept generic (any module, not just those two)
    in case a future stage needs the same "external filter, teed to
    disk" shape.
    """
    with src.open("rb") as fin, dst.open("wb") as fout:
        _ = chatfs_sh.run([sys.executable, "-m", module], stdin=fin, stdout=fout)


def browse(url: str, dst: Path) -> None:
    """Run har-browse against url, writing its CDP capture (jsonl) to dst."""
    chatfs_sh.log(f"Capturing {url} → {dst} ...")
    with dst.open("wb") as f:
        _ = chatfs_sh.run(["har-browse", url], stdout=f)


def dump_jsonl(values: Iterable[JsonValue], out: TextIO) -> None:
    for value in values:
        _ = out.write(json.dumps(value) + "\n")


def pluck(
    fn: Callable[[Iterable[str]], Iterator[JsonValue]], src: Path, dst: Path
) -> None:
    """Run a plucking generator over src's lines; write its yields as JSONL to dst.

    `fn` is `chatfs.pluck.iter_response_bodies` (or a provider's thin
    wrapper around it). Creates `dst`'s parent so callers can freely
    target a not-yet-existing `X.d/` scratch dir (`path-ownership.md`)
    without a separate mkdir at each call site.
    """
    chatfs_sh.log(f"Plucking → {dst} ...")
    dst.parent.mkdir(parents=True, exist_ok=True)
    with src.open() as fin, dst.open("w") as fout:
        dump_jsonl(fn(fin), fout)


def capture(
    url: str,
    chat_dir: Path,
    pluck_fn: Callable[[Iterable[str]], Iterator[JsonValue]],
    *,
    conversation_filename: str = "conversation.json",
) -> Path:
    """Browse $url and pluck the conversation into `.data/$UUID/`.

    Ensures the data dir exists, then stages each output (`cdp.jsonl`,
    `conversation_filename`) at a hidden scratch sibling and atomically
    promotes it -- the prior artifact is only replaced once its
    successor is fully written. A failed browse (the one stage most
    likely to fail, and the one artifact class that isn't locally
    re-derivable) leaves the prior `cdp.jsonl` untouched instead of
    destroying it; the partial attempt is preserved as a `.fail`
    sibling. Both promotions share one outer write lock on the data
    dir, so a cooperating reader (`chatfs.shell.locks.read_locked`) never
    observes cdp.jsonl and the conversation as a mismatched pair from
    two different runs. Returns the data dir for callers that need to
    deposit meta.json or similar siblings. Does not touch `chat_dir`
    itself -- `.chat/$UUID/` may not exist yet (see chatfs.layout's
    module docstring); only its `data_dir_of` twin is written here.

    `pluck_fn` and `conversation_filename` are the provider-shaped
    half: each provider's leaf entry points supply their own
    conversation pluck, and name its output `conversation.json.d/raw.*`
    instead of the default `conversation.json` whenever that pluck
    output needs a stage of its own before it earns the contract name
    (AI Studio's massage, chatgpt's assemble). The `.d/` scratch
    convention is `path-ownership.md`'s: a top-level contract name `X`
    reserves the sibling `X.d/` for scratch involved in producing or
    checking it.

    The intermediate-data policy is the load-bearing piece: captures
    land directly in `.data/$UUID/`, never a tempdir. Failures leave
    the bytes inspectable; success hands off to splat/render without a
    move.
    """
    data_dir = data_dir_of(chat_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    cdp = data_dir / "cdp.jsonl"
    conversation = data_dir / conversation_filename

    with chatfs_locks.write_locked(data_dir):
        with chatfs_atomic.staged(cdp, anchor=data_dir) as tmp:
            browse(url, tmp)
        with chatfs_atomic.staged(conversation, anchor=data_dir) as tmp:
            pluck(pluck_fn, cdp, tmp)

    return data_dir


def captured_at(chat_dir: Path) -> datetime | None:
    """When this chat was last captured, or None if it never was.

    Read from `conversation.json`'s mtime. That file is written by one
    stage and atomically promoted only once the capture succeeded (see
    `capture`), so its mtime is a completed capture's finish time rather
    than the moment some partial attempt started -- which is what makes
    a bare mtime trustworthy as a watermark.
    """
    conversation = data_dir_of(chat_dir) / "conversation.json"
    if not conversation.exists():
        return None
    return datetime.fromtimestamp(conversation.stat().st_mtime, UTC)
