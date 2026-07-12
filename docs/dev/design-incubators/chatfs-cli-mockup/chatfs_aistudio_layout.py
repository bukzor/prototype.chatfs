"""Provider adapter for the AI Studio mockup — see chatfs_layout for the
shared storage/view-tree helpers this wraps.

AI Studio's twist: the source is JSPB (positional arrays), so the
identity fields are *synthesized* into an `IndexItem` (`index_item`)
from chatfs_aistudio_conversation_massage_json's named projection,
rather than passed through from a native dict.
"""

from datetime import datetime, timezone
from pathlib import Path

from chatfs_aistudio_types import Conversation, IndexItem
from chatfs_layout import DATA_DIR_NAME, chat_dir_for, data_dir_for
from chatfs_layout import capture as _capture
from chatfs_layout import place_meta as _place_meta
from chatfs_layout import resolve_chat_dir, safe_filename

__all__ = [
    "DATA_DIR_NAME",
    "chat_dir_for",
    "data_dir_for",
    "resolve_chat_dir",
    "safe_filename",
    "capture",
    "index_item",
    "place_meta",
]

HERE = Path(__file__).parent
CONVERSATION_PLUCK = HERE / "chatfs_aistudio_conversation_pluck.jq"


def capture(url: str, chat_dir: Path) -> Path:
    """Browse $url and pluck the raw JSPB doc — massage is a separate stage.

    `conversation.raw.json`, not `conversation.json`: unlike
    chatgpt/claude, AI Studio's pluck output isn't yet named — see
    `chatfs_aistudio_conversation_massage_json.py`.
    """
    return _capture(url, chat_dir, CONVERSATION_PLUCK, conversation_filename="conversation.raw.json")


def index_item(doc: Conversation) -> IndexItem:
    """Synthesize the identity fields from the massaged conversation doc.

    The provider-shaped half of the layout boundary: where chatgpt and
    claude read keyed fields off a native dict, AI Studio's wire format
    is positional (see chatfs_aistudio_conversation_massage_json, the
    only place those positions are named), so identity is synthesized
    here from its named output instead. `prompt.name` is
    `"prompts/<id>"`; the `prompts/` prefix is dropped so the id matches
    the URL/Drive id.

    Two provenances feed this function through the same `Conversation`
    shape — both decode via the identical PROMPT/METADATA jspb schema
    (cross-checked in ../aistudio-schema/rosetta/'s ListPrompts golden
    pair, which shares this schema with ResolveDriveResource's):

    - A full `ResolveDriveResource` fetch: `chunkedPrompt.chunks` is
      populated, so `create_time` — the first chunk's true `createTime`
      (a `[seconds-string, nanos]` pair) — is known. This matches
      chatgpt/claude's semantic (their index date-trees also bucket by
      creation).
    - A `ListPrompts` index entry: `chunkedPrompt` is present but
      *empty* — the index carries no turn content — so `create_time`
      can't be derived at all. `metadata.lastModified.revisionTime` is
      always present but is NOT creation time (it advances on every
      turn — verified: it trails the last chunk's createTime in a live
      capture); per no-partial-synthesis.md we don't launder it into
      `create_time`. It's recorded honestly as `last_modified` instead,
      and `create_time` is simply omitted (NotRequired) — see
      `place_meta`, which reflects the difference in the view tree.
    """
    prompt = doc["prompt"]
    raw_id = prompt["name"]
    assert raw_id.startswith("prompts/"), raw_id
    metadata = prompt["metadata"]
    item = IndexItem(
        id=raw_id.removeprefix("prompts/"),
        title=metadata["displayName"],
        last_modified=int(metadata["lastModified"]["revisionTime"][0]),
    )
    chunks = prompt["chunkedPrompt"].get("chunks")
    if chunks:
        item["create_time"] = int(chunks[0]["createTime"][0])
    return item


def _created(unix_seconds: int) -> datetime:
    """Parse one of AI Studio's unix-seconds timestamp fields.

    Shared by create_time and last_modified — same jspb shape, coerced
    to int the same way (see index_item). No ISO-string variant to
    handle (cf. chatgpt, which returns both shapes).
    """
    return datetime.fromtimestamp(unix_seconds, tz=timezone.utc)


def place_meta(item: IndexItem, root: Path) -> Path:
    """Write meta.json into .chat/$UUID/.data/, refresh the view dir-symlink.

    View-tree placement prefers true creation time when `index_item`
    found one (`Created=`-labeled year segment, time_dir_for's
    default); falls back to `last_modified` under `LastModified=`
    otherwise, so the date tree never implies a creation-time claim
    this entry can't back up. A later `place_meta` call for the same id
    with real `create_time` — e.g. once the conversation is actually
    fetched — purges the old labeled symlink (identity-scoped cleanup,
    shared place_meta) and re-places it under `Created=`: this entry
    "graduates."

    Returns the chat dir.
    """
    if "create_time" in item:
        created, label = _created(item["create_time"]), "Created"
    else:
        created, label = _created(item["last_modified"]), "LastModified"
    return _place_meta(item["id"], item["title"], created, item, root, label=label)
