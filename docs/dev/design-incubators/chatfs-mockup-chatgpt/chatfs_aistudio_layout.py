"""Provider adapter for the AI Studio mockup — see chatfs_layout for the
shared storage/view-tree helpers this wraps.

AI Studio's twist: the source is JSPB (positional arrays), so the
identity fields are *synthesized* into an `IndexItem` (`index_item`)
from chatfs_aistudio_conversation_massage_json's named projection,
rather than passed through from a native dict.
"""

from datetime import datetime, timezone
from pathlib import Path

from chatfs_aistudio_types import IndexItem
from chatfs_layout import (
    DATA_DIR_NAME,
    chat_dir_for,
    data_dir_for,
    resolve_chat_dir,
    safe_filename,
)
from chatfs_layout import place_meta as _place_meta

__all__ = [
    "DATA_DIR_NAME",
    "chat_dir_for",
    "data_dir_for",
    "resolve_chat_dir",
    "safe_filename",
    "index_item",
    "place_meta",
]


def index_item(doc: dict) -> IndexItem:
    """Synthesize the identity fields from the massaged conversation doc.

    The provider-shaped half of the layout boundary: where chatgpt and
    claude read keyed fields off a native dict, AI Studio's wire format
    is positional (see chatfs_aistudio_conversation_massage_json, the
    only place those positions are named), so identity is synthesized
    here from its named output instead. `prompt.name` is
    `"prompts/<id>"`; the `prompts/` prefix is dropped so the id matches
    the URL/Drive id.

    create_time is the first chunk's `createTime` (a `[seconds-string,
    nanos]` pair), coerced to int seconds — true creation time, matching
    chatgpt/claude's semantic (their index date-trees also bucket by
    creation). `metadata.lastModified.revisionTime` is NOT creation
    time — it advances on every turn (verified: it trails the last
    chunk's createTime in a live capture) — and is deliberately not used
    here, so AI Studio's date tree stays comparable to the other two
    providers'. There is no separate modified_time field (neither
    chatgpt's nor claude's IndexItem carries one either).
    """
    prompt = doc["prompt"]
    raw_id = prompt["name"]
    assert isinstance(raw_id, str) and raw_id.startswith("prompts/"), raw_id
    metadata = prompt["metadata"]
    chunks = prompt["chunkedPrompt"]["chunks"]
    assert chunks, "empty chunkedPrompt.chunks: no first-chunk createTime to anchor on"
    create_time = chunks[0]["createTime"]
    return IndexItem(
        id=raw_id.removeprefix("prompts/"),
        title=metadata["displayName"],
        create_time=int(create_time[0]),
    )


def _created(create_time: int) -> datetime:
    """Parse AI Studio's created field — unix seconds only.

    No ISO-string variant to handle (cf. chatgpt, which returns both
    shapes).
    """
    return datetime.fromtimestamp(create_time, tz=timezone.utc)


def place_meta(item: IndexItem, root: Path) -> Path:
    """Write meta.json into .chat/$UUID/.data/, refresh the view dir-symlink.

    Returns the chat dir.
    """
    return _place_meta(item["id"], item["title"], _created(item["create_time"]), item, root)
