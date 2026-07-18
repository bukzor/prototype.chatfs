"""Shared layout helpers, factored out of the three provider layouts.

Storage is flat and UUID-keyed, split by lifecycle into two parallel
trees:

    $root/.data/$UUID/       # captured exhaust -- input, never purged
        meta.json
        conversation.json
        conversation.json.d/raw.json  # AI Studio only: pre-massage pluck
        cdp.jsonl
        cdp.jsonl.d/index-pages.jsonl # chatgpt/claude only: cross-check dump
    $root/.chat/$UUID/       # 100% derived -- THE staged/promoted unit
        chat.md
        messages/            # derived (splat output)
        conversations/       # derived (splat output)
        .data -> ../../.data/$UUID   # inspection symlink

`.chat/$UUID/` does not exist before first render -- only `.data/$UUID/`
does. `resolve_chat_dir` and the view dir-symlink both tolerate this
(see their own docstrings).

The view tree at $root/YYYY/MM/DD/HH:MM:SS±HH:MM/$TITLE/ is a single
directory-symlink per chat pointing at `.chat/$UUID/`. See
design.kb/040-design.kb/chat-as-directory.md.

Provider-shaped work (parsing a provider's own timestamp shape into a
tz-aware `datetime`, reading a provider's own IndexItem key names, and
naming a provider's own conversation pluck script) stays in each
`chatfs_<provider>_layout.py`'s thin `capture()`/`place_meta()`
wrappers; everything below is byte-for-byte identical across
chatgpt/claude/aistudio.
"""

import json
import os
import re
import subprocess
import sys
from collections.abc import Callable, Iterable, Iterator, Mapping
from datetime import datetime
from pathlib import Path
from typing import TextIO

import chatfs_json
from chatfs_json import JsonValue

DATA_DIR_NAME = ".data"


def safe_filename(name: str) -> str:
    return name.replace("/", "∕").replace("\x00", "")


def _iso_offset(dt: datetime) -> str:
    """Return ISO 8601 extended-form offset, e.g. '-05:00'.

    Computed directly from utcoffset() to avoid the glibc-only %:z and
    Python's variable-length %z (which can include seconds).
    """
    off = dt.utcoffset()
    assert off is not None, dt
    total_min = int(off.total_seconds() // 60)
    sign = "+" if total_min >= 0 else "-"
    h, m = divmod(abs(total_min), 60)
    return f"{sign}{h:02d}:{m:02d}"


def time_dir_for(created: datetime, *, label: str = "Created") -> Path:
    """Render an ISO 8601 path-friendly timestamp in system local time.

    Takes an already-parsed, tz-aware datetime — parsing a provider's
    own wire-format timestamp (ISO string, unix float, unix int-string,
    ...) into one is provider-shaped and lives in that provider's
    `_created()`.

    `label` prefixes the year segment as `f"{label}={year}"` — every
    date-based view is labeled, uniformly, with what the timestamp
    actually is (`Created=`, the default, for true creation time;
    `LastModified=` when that's all a provider's capture can supply).
    Multiple date-based views can then coexist under `root` without
    colliding or implying a claim they can't back up. See
    `design.kb/040-design.kb/no-partial-synthesis.md`.
    """
    dt = created.astimezone()
    return Path(f"{label}={dt:%Y}/{dt:%m/%d/%H:%M:%S}{_iso_offset(dt)}")


def chat_dir_for(uuid: str, root: Path) -> Path:
    return root / ".chat" / uuid


def data_dir_for(uuid: str, root: Path) -> Path:
    return root / DATA_DIR_NAME / uuid


def data_dir_of(chat_dir: Path) -> Path:
    """The `.data/$UUID/` twin for a `.chat/$UUID/` dir.

    Derives root and uuid from chat_dir's own path -- chat_dir_for's
    shape (`root/.chat/$UUID`) is preserved by resolve_chat_dir too, so
    this works on any chat_dir a caller has in hand without threading
    root through separately.
    """
    return data_dir_for(chat_dir.name, chat_dir.parent.parent)


def link_data_dir(dst: Path, uuid: str) -> None:
    """Create/refresh `dst/.data` as a symlink to `.data/$UUID`.

    Fixed relative target (`../../.data/$UUID`), valid unchanged
    whether `dst` is the final chat_dir (`root/.chat/$UUID/`) or a
    same-depth staged scratch sibling (`root/.chat/.{$UUID}.tmp/`) --
    both sit two levels below `root`. `uuid` is taken explicitly rather
    than `dst.name`, since that assumption breaks for the scratch case.
    """
    link = dst / DATA_DIR_NAME
    if link.is_symlink() or link.exists():
        link.unlink()
    link.symlink_to(Path("..", "..", DATA_DIR_NAME, uuid))


def resolve_chat_dir(arg: str | os.PathLike[str]) -> Path:
    """Resolve any path-into-or-pointing-at a `.chat/$UUID/` to that dir.

    Handles: the chat dir itself, files or subdirs inside it, its
    `.data` inspection symlink (and paths descending through it into
    the real `.data/$UUID/` tree), a `.data/$UUID/` path reached
    directly, view dir-symlinks, and paths descending through view
    dir-symlinks (e.g. `view/$TITLE/.data/foo`) -- climbing by
    `p.parent.name` rather than `is_dir()`, so a not-yet-rendered
    (nonexistent) chat_dir or a dangling view symlink resolves
    correctly instead of requiring existence.

    Does not assert the result exists: `.chat/$UUID/` legitimately
    doesn't, before first render (see module docstring). Callers that
    need captured state present check for it explicitly (e.g. via
    `data_dir_of`).
    """
    p = Path(arg).resolve()
    while True:
        if p.parent.name == ".chat":
            return p
        if p.parent.name == ".data":
            return chat_dir_for(p.name, p.parent.parent)
        assert p.parent != p, f"reached fs root without finding .chat or .data: {arg}"
        p = p.parent


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
        _ = subprocess.run([str(script)], stdin=fin, stdout=fout, check=True)


def iter_responses_matching(
    cdp_lines: Iterable[str], url_pattern: re.Pattern[str]
) -> Iterator[JsonValue]:
    """Filter CDP capture lines to matching `Network.responseReceived` bodies.

    The skeleton shared by every provider's conversation/index pluck:
    select events whose response URL matches `url_pattern`, then
    string-guard the body before parsing it as JSON — a 204 or
    interrupted response carries a non-string (`null`) body, so it's
    silently skipped here, same as the old `*.jq` filters' `| strings |`
    stage skipped it.

    Yields one parsed body per matching event; a provider's own pluck
    wrapper handles any further per-provider reshaping (AI Studio's
    envelope flatten/guard; see `chatfs_aistudio_layout.py`).
    """
    for line in cdp_lines:
        if not line.strip():
            continue
        event = chatfs_json.loads(line)
        assert isinstance(event, dict), event
        if event.get("method") != "Network.responseReceived":
            continue
        params = event["params"]
        assert isinstance(params, dict), params
        response = params["response"]
        assert isinstance(response, dict), response
        url = response["url"]
        assert isinstance(url, str), url
        if not url_pattern.search(url):
            continue
        body = response.get("body")
        if not isinstance(body, str):
            continue
        yield chatfs_json.loads(body)


def browse(url: str, dst: Path) -> None:
    """Run har-browse against url, writing its CDP capture (jsonl) to dst."""
    print(f"Capturing {url} → {dst} ...", file=sys.stderr)
    with dst.open("wb") as f:
        _ = subprocess.run(["har-browse", url], stdout=f, check=True)


def dump_jsonl(values: Iterable[JsonValue], out: TextIO) -> None:
    for value in values:
        _ = out.write(json.dumps(value) + "\n")


def pluck(
    fn: Callable[[Iterable[str]], Iterator[JsonValue]], src: Path, dst: Path
) -> None:
    """Run a plucking generator over src's lines; write its yields as JSONL to dst.

    Pure-Python counterpart to `run_pluck`: `fn` is `iter_responses_matching`
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

    Ensures the data dir exists, clears any prior cdp.jsonl /
    `conversation_filename` from a previous run, then runs har-browse
    followed by `pluck_fn`. Returns the data dir for callers that
    need to deposit meta.json or similar siblings. Does not touch
    `chat_dir` itself -- `.chat/$UUID/` may not exist yet (see module
    docstring); only its `data_dir_of` twin is written here.

    `pluck_fn` and `conversation_filename` are the provider-shaped
    half: each provider's `capture()` wrapper supplies its own
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

    cdp.unlink(missing_ok=True)
    conversation.unlink(missing_ok=True)

    browse(url, cdp)
    pluck(pluck_fn, cdp, conversation)

    return data_dir


def _purge_view_symlinks(uuid: str, root: Path) -> None:
    """Remove every view-tree symlink under `root` whose target mentions
    `uuid`.

    Identity-scoped cleanup: derived view paths can move when
    derivation logic changes (TZ format, view shape); we sweep by
    identity, not path. Skips `.chat/` and `.data/` -- those hold
    storage-internal symlinks (e.g. `.chat/$UUID/.data`'s inspection
    link back to `.data/$UUID/`), not views, and their targets
    legitimately contain the uuid too.
    """
    for path in root.rglob("*"):
        rel_parts = path.relative_to(root).parts
        if ".chat" in rel_parts or ".data" in rel_parts:
            continue
        if path.is_symlink() and uuid in os.readlink(path):
            path.unlink()


def place_meta(
    id: str,
    title: str,
    created: datetime,
    item: Mapping[str, object],
    root: Path,
    *,
    label: str = "Created",
) -> Path:
    """Write meta.json into `.data/$UUID/`, refresh the view dir-symlink.

    `item` is serialized verbatim into meta.json (the provider's full
    index entry, pass-through fields included); `id`/`title`/`created`
    are the already-extracted identity fields a provider's place_meta
    wrapper pulls out of it. Falls back to `id` when `title` is empty,
    so an empty-titled chat never collapses its view symlink onto
    `view_dir` itself.

    `label` forwards to `time_dir_for` — see there. Storage placement
    (`.data/$UUID/`) and the identity-scoped symlink purge are
    unaffected by it: only the derived view-tree segment changes, so a
    later `place_meta` call with real creation time (different `label`)
    still finds and replaces this call's symlink by uuid, moving the
    chat from the labeled tree to the true date tree.

    Does not touch `.chat/$UUID/` -- it may not exist yet (see module
    docstring); that's render's job. Returns the (possibly
    not-yet-existing) chat dir, for callers that pass it on to render.
    """
    chat_dir = chat_dir_for(id, root)
    data_dir = data_dir_for(id, root)
    data_dir.mkdir(parents=True, exist_ok=True)
    _ = (data_dir / "meta.json").write_text(json.dumps(item, indent=2) + "\n")

    _purge_view_symlinks(id, root)

    view_dir = root / time_dir_for(created, label=label)
    view_dir.mkdir(parents=True, exist_ok=True)

    title_link = view_dir / safe_filename(title or id)
    if title_link.is_symlink() or title_link.exists():
        title_link.unlink()
    title_link.symlink_to(os.path.relpath(chat_dir, start=view_dir))

    return chat_dir
