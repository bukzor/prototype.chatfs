"""Shared layout helpers for the AI Studio mockup.

Third mirror of chatfs_chatgpt_layout.py / chatfs_claude_layout.py. The
storage and view shapes are identical (`.chat/$UUID/.data/` + a view
dir-symlink per chat); only the item keys differ.

AI Studio's twist: the source is JSPB (positional arrays), so the
identity fields are *synthesized* into an `IndexItem` (`index_item`)
from chatfs_aistudio_conversation_massage_json's named projection,
rather than passed through from a native dict. Once that synthesis
happens, place_meta is byte-for-byte the chatgpt path — which is
exactly the seam a shared `chatfs_layout.py` would cut along.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from chatfs_aistudio_types import IndexItem

DATA_DIR_NAME = ".data"


def index_item(doc: dict) -> IndexItem:
    """Synthesize the identity fields from the massaged conversation doc.

    The provider-shaped half of the layout boundary: where chatgpt and
    claude read keyed fields off a native dict, AI Studio's wire format
    is positional (see chatfs_aistudio_conversation_massage_json, the
    only place those positions are named), so identity is synthesized
    here from its named output instead. `prompt.name` is
    `"prompts/<id>"`; the `prompts/` prefix is dropped so the id matches
    the URL/Drive id. The create_time field is `lastModified.revisionTime`
    (a `[seconds-string, nanos]` pair), coerced to int seconds.
    """
    prompt = doc["prompt"]
    raw_id = prompt["name"]
    assert isinstance(raw_id, str) and raw_id.startswith("prompts/"), raw_id
    metadata = prompt["metadata"]
    revision_time = metadata["lastModified"]["revisionTime"]
    return IndexItem(
        id=raw_id.removeprefix("prompts/"),
        title=metadata["displayName"],
        create_time=int(revision_time[0]),
    )


def safe_filename(name: str) -> str:
    return name.replace("/", "∕").replace("\x00", "")


def _iso_offset(dt: datetime) -> str:
    off = dt.utcoffset()
    assert off is not None, dt
    total_min = int(off.total_seconds() // 60)
    sign = "+" if total_min >= 0 else "-"
    h, m = divmod(abs(total_min), 60)
    return f"{sign}{h:02d}:{m:02d}"


def time_dir_for(create_time: float) -> Path:
    """ISO 8601 path-friendly timestamp in system local time.

    AI Studio's created field is unix seconds only — no ISO-string
    variant to handle (cf. chatgpt, which returns both shapes).
    """
    dt = datetime.fromtimestamp(create_time, tz=timezone.utc).astimezone()
    return Path(f"{dt:%Y/%m/%d/%H:%M:%S}{_iso_offset(dt)}")


def chat_dir_for(uuid: str, root: Path) -> Path:
    return root / ".chat" / uuid


def data_dir_for(uuid: str, root: Path) -> Path:
    return chat_dir_for(uuid, root) / DATA_DIR_NAME


def resolve_chat_dir(arg: str | os.PathLike[str]) -> Path:
    p = Path(arg).resolve()
    if not p.is_dir():
        p = p.parent
    while p.parent.name != ".chat":
        assert p.parent != p, f"reached fs root without finding .chat: {arg}"
        p = p.parent
    assert p.is_dir(), p
    return p


def _purge_view_symlinks(uuid: str, root: Path) -> None:
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
    _ = (data_dir / "meta.json").write_text(json.dumps(item, indent=2) + "\n")

    _purge_view_symlinks(uuid, root)

    view_dir = root / time_dir_for(item["create_time"])
    view_dir.mkdir(parents=True, exist_ok=True)

    title_link = view_dir / safe_filename(item["title"] or uuid)
    if title_link.is_symlink() or title_link.exists():
        title_link.unlink()
    title_link.symlink_to(os.path.relpath(chat_dir, start=view_dir))

    return chat_dir
