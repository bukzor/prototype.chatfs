"""Shared layout helpers for the chatgpt mockup.

Storage is flat and UUID-keyed:

    $root/.chat/$UUID/
        chat.md          # derived
        messages/        # derived (chatgpt-splat output)
        conversations/   # derived (chatgpt-splat output)
        .data/           # captured exhaust (hidden from default ls)
            meta.json
            conversation.json
            cdp.jsonl

The view tree at $root/YYYY/MM/DD/HH:MM:SS±HH:MM/$TITLE/ is a single
directory-symlink per chat pointing at `.chat/$UUID/`. See
design.kb/040-design.kb/chat-as-directory.md.
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from chatfs_chatgpt_types import IndexItem


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


def time_dir_for(create_time: str | float) -> Path:
    """Render an ISO 8601 path-friendly timestamp in system local time.

    Accepts both shapes ChatGPT returns:
    - str: index endpoint, e.g. '2026-04-15T14:53:42.270850Z'
    - float: conversation document, Unix seconds
    """
    if isinstance(create_time, (int, float)):
        dt = datetime.fromtimestamp(create_time, tz=timezone.utc).astimezone()
    else:
        dt = datetime.fromisoformat(create_time.replace("Z", "+00:00")).astimezone()
    return Path(f"{dt:%Y/%m/%d/%H:%M:%S}{_iso_offset(dt)}")


def chat_dir_for(uuid: str, root: Path) -> Path:
    return root / ".chat" / uuid


def data_dir_for(uuid: str, root: Path) -> Path:
    return chat_dir_for(uuid, root) / DATA_DIR_NAME


def resolve_chat_dir(arg: str | os.PathLike) -> Path:
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


def place_meta(item: IndexItem, root: Path) -> Path:
    """Write meta.json into .chat/$UUID/.data/, refresh the view dir-symlink.

    Returns the chat dir.
    """
    uuid = item["id"]
    chat_dir = chat_dir_for(uuid, root)
    data_dir = chat_dir / DATA_DIR_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "meta.json").write_text(json.dumps(item, indent=2) + "\n")

    _purge_view_symlinks(uuid, root)

    view_dir = root / time_dir_for(item["create_time"])
    view_dir.mkdir(parents=True, exist_ok=True)

    title_link = view_dir / safe_filename(item["title"])
    if title_link.is_symlink() or title_link.exists():
        title_link.unlink()
    title_link.symlink_to(os.path.relpath(chat_dir, start=view_dir))

    return chat_dir
