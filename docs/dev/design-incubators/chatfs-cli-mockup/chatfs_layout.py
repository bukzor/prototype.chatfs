"""Shared layout helpers, factored out of the three provider layouts.

Storage is flat and UUID-keyed:

    $root/.chat/$UUID/
        chat.md          # derived
        messages/        # derived (splat output)
        conversations/   # derived (splat output)
        .data/           # captured exhaust (hidden from default ls)
            meta.json
            conversation.json (or conversation.raw.json + conversation.json)
            cdp.jsonl

The view tree at $root/YYYY/MM/DD/HH:MM:SS±HH:MM/$TITLE/ is a single
directory-symlink per chat pointing at `.chat/$UUID/`. See
design.kb/040-design.kb/chat-as-directory.md.

Provider-shaped work (parsing a provider's own timestamp shape into a
tz-aware `datetime`, and reading a provider's own IndexItem key names)
stays in each `chatfs_<provider>_layout.py`; everything below is
byte-for-byte identical across chatgpt/claude/aistudio.
"""
import json
import os
from collections.abc import Mapping
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
    return chat_dir_for(uuid, root) / DATA_DIR_NAME


def resolve_chat_dir(arg: str | os.PathLike[str]) -> Path:
    """Resolve any path-into-or-pointing-at a `.chat/$UUID/` to that dir.

    Handles: the chat dir itself, files or subdirs inside it, view
    dir-symlinks (which resolve straight to the chat dir), and paths
    descending through view dir-symlinks (e.g. `view/$TITLE/.data/foo`).

    Asserts the result is an existing `.chat/$UUID/` directory so that
    callers can treat the return value as canonical and fail loudly on
    bad input here rather than later via missing-file errors.
    """
    p = Path(arg).resolve()
    if not p.is_dir():
        p = p.parent
    while p.parent.name != ".chat":
        assert p.parent != p, f"reached fs root without finding .chat: {arg}"
        p = p.parent
    assert p.is_dir(), p
    return p


def _purge_view_symlinks(uuid: str, root: Path) -> None:
    """Remove every symlink under `root` whose target mentions `uuid`.

    Identity-scoped cleanup: derived view paths can move when
    derivation logic changes (TZ format, view shape); we sweep by
    identity, not path.
    """
    for path in root.rglob("*"):
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
    """Write meta.json into .chat/$UUID/.data/, refresh the view dir-symlink.

    `item` is serialized verbatim into meta.json (the provider's full
    index entry, pass-through fields included); `id`/`title`/`created`
    are the already-extracted identity fields a provider's place_meta
    wrapper pulls out of it. Falls back to `id` when `title` is empty,
    so an empty-titled chat never collapses its view symlink onto
    `view_dir` itself.

    `label` forwards to `time_dir_for` — see there. Storage placement
    (`.chat/$UUID/`) and the identity-scoped symlink purge are
    unaffected by it: only the derived view-tree segment changes, so a
    later `place_meta` call with real creation time (different `label`)
    still finds and replaces this call's symlink by uuid, moving the
    chat from the labeled tree to the true date tree.

    Returns the chat dir.
    """
    chat_dir = chat_dir_for(id, root)
    data_dir = chat_dir / DATA_DIR_NAME
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
