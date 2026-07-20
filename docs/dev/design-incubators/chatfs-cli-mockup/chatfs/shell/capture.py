"""Capture: browse + pluck, landing exhaust into `.data/$UUID/`.

Exception to chatfs/'s purity rule (see chatfs.shell's package docstring):
every function here does real I/O -- subprocess, filesystem, or both.
"""

import json
import sys
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path
from typing import TextIO

from chatfs.json import JsonValue
from chatfs.layout import data_dir_of
from chatfs.shell import atomic as chatfs_atomic
from chatfs.shell import locks as chatfs_locks
from chatfs.shell import sh as chatfs_sh


def run_pluck(script: Path, src: Path, dst: Path) -> None:
    """Run an external filter script: read src, write its stdout to dst.

    Shared low-level primitive behind every remaining "tee the filtered
    stream to disk" step that still shells out to a separate script —
    today, only AI Studio's massage stage (`conversation.json.d/raw.json`
    -> `conversation.json`), since every provider's conversation/index pluck
    is now an in-process generator run through `pluck()` instead. Kept
    generic (any script, not just massage) in case a future stage needs
    the same "external filter, teed to disk" shape.
    """
    with src.open("rb") as fin, dst.open("wb") as fout:
        _ = chatfs_sh.run([str(script)], stdin=fin, stdout=fout)


def browse(url: str, dst: Path) -> None:
    """Run har-browse against url, writing its CDP capture (jsonl) to dst."""
    print(f"Capturing {url} → {dst} ...", file=sys.stderr)
    with dst.open("wb") as f:
        _ = chatfs_sh.run(["har-browse", url], stdout=f)


def dump_jsonl(values: Iterable[JsonValue], out: TextIO) -> None:
    for value in values:
        _ = out.write(json.dumps(value) + "\n")


def pluck(
    fn: Callable[[Iterable[str]], Iterator[JsonValue]], src: Path, dst: Path
) -> None:
    """Run a plucking generator over src's lines; write its yields as JSONL to dst.

    Pure-Python counterpart to `run_pluck`: `fn` is `chatfs.pluck.iter_responses_matching`
    (or a provider's thin wrapper around it) in place of an external
    filter script/subprocess. Creates `dst`'s parent so callers can freely
    target a not-yet-existing `X.d/` scratch dir (`path-ownership.md`)
    without a separate mkdir at each call site.
    """
    print(f"Plucking → {dst} ...", file=sys.stderr)
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
    conversation pluck (and, for AI Studio, `conversation.json.d/raw.json`
    instead of the default `conversation.json`, since that provider's
    pluck output still needs a massage pass before it's named — the `.d/`
    scratch convention is `path-ownership.md`'s: a top-level contract
    name `X` reserves the sibling `X.d/` for scratch involved in
    producing or checking it).

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
