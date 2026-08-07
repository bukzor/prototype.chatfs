"""Shared path vocabulary, factored out of the three provider layouts.

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
does. `resolve_chat_dir` (chatfs.shell.place) and the view dir-symlink
both tolerate this (see their own docstrings).

The view tree at $root/YYYY/MM/DD/HH:MM:SS±HH:MM/$TITLE/ is a single
directory-symlink per chat pointing at `.chat/$UUID/`. See
design.kb/040-design.kb/chat-as-directory.md.

This module is pure path arithmetic -- no filesystem access, no
subprocess. `chatfs.pluck` holds the shared CDP-filtering skeleton;
`chatfs.shell.capture`/`chatfs.shell.place` hold the side-effecting
operations built on both. Provider-shaped work (parsing a provider's own
timestamp shape, URL <-> uuid conversion) lives in each
`chatfs.provider.<name>.layout`.
"""

from datetime import datetime
from pathlib import Path

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
    `created_at()`.

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
