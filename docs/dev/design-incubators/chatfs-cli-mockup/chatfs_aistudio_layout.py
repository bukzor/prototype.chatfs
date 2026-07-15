"""Provider adapter for the AI Studio mockup — see chatfs_layout for the
shared storage/view-tree helpers this wraps.

AI Studio's twist: the source is JSPB (positional arrays), so the
identity fields are *synthesized* into an `IndexItem` (`index_item`)
from chatfs_aistudio_conversation_massage_json's named projection,
rather than passed through from a native dict.
"""

import re
from collections.abc import Iterable, Iterator
from datetime import datetime, timezone
from pathlib import Path

from chatfs_aistudio_types import Conversation, IndexItem
from chatfs_json import JsonValue, is_json_array
from chatfs_layout import DATA_DIR_NAME, chat_dir_for, data_dir_for
from chatfs_layout import capture as _capture
from chatfs_layout import iter_responses_matching, place_meta as _place_meta
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
    "pluck_conversation",
    "pluck_index_pages",
]

# ResolveDriveResource resolves any Drive resource, not just prompts, so URL
# alone doesn't guarantee a prompt body — pluck_conversation guards on shape
# too.
CONVERSATION_URL = re.compile(r"[./]MakerSuiteService/ResolveDriveResource$")
INDEX_URL = re.compile(r"[./]MakerSuiteService/ListPrompts$")


def pluck_conversation(cdp_lines: Iterable[str]) -> Iterator[JsonValue]:
    """Pluck each prompt message out of a ResolveDriveResource response body.

    AI Studio prompts are Drive-backed; the whole conversation arrives in
    this RPC as application/json+protobuf (JSPB — positional arrays, not
    keyed objects). Guards on shape, not just URL: the first message's
    `[0]` is `"prompts/<id>"`; yielding each envelope element flattens to
    one message per line (mirrors the old `.jq`'s `.[]`).
    """
    for envelope in iter_responses_matching(cdp_lines, CONVERSATION_URL):
        assert is_json_array(envelope), envelope
        first = envelope[0] if envelope else None
        first_id = first[0] if is_json_array(first) and first else ""
        if not (isinstance(first_id, str) and first_id.startswith("prompts/")):
            continue
        yield from envelope


def pluck_index_pages(cdp_lines: Iterable[str]) -> Iterator[JsonValue]:
    """Pluck each ListPrompts index entry, one per line.

    A response body is the JSPB envelope `[[<entry>, ...]]`; flattening
    `envelope[0]` yields individual entries so downstream doesn't need to
    know how many response bodies were captured (i.e. doesn't need to
    care about pagination — see chatfs_aistudio_index_splat.py). Entries
    share ResolveDriveResource's PROMPT/METADATA schema (see
    chatfs_aistudio_conversation_massage_json) with an empty
    chunkedPrompt (index entries carry no turn content).
    """
    for envelope in iter_responses_matching(cdp_lines, INDEX_URL):
        assert is_json_array(envelope) and envelope, envelope
        entries = envelope[0]
        assert is_json_array(entries), entries
        yield from entries


def capture(url: str, chat_dir: Path) -> Path:
    """Browse $url and pluck the raw JSPB doc — massage is a separate stage.

    `conversation.json.d/raw.json`, not `conversation.json`: unlike
    chatgpt/claude, AI Studio's pluck output isn't yet named, so it's
    scratch reserved under the eventual contract file's `.d/` sibling
    (`path-ownership.md`) rather than a second contract name — see
    `chatfs_aistudio_conversation_massage_json.py`.
    """
    return _capture(
        url, chat_dir, pluck_conversation, conversation_filename="conversation.json.d/raw.json"
    )


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
