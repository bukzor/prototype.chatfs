#!/usr/bin/env python3
"""Splat AI Studio ListPrompts index entries into per-chat storage.

Usage:
    python -m chatfs.provider.aistudio.index.splat

Reads one index entry per line on stdin —
chatfs.provider.aistudio.pluck.pluck_index_pages's output. Pluck already
flattens each response's entry list, so this script never sees a
page/envelope shape and doesn't need to know or care how many
ListPrompts responses were captured — one page or many (pagination),
each entry just arrives as its own line.

Each entry is massaged through the same PROMPT schema ResolveDriveResource
uses (verified: entries decode with it unchanged, just with an empty
chunkedPrompt — no turn content on an index-only entry), then handed to
index_item/place_meta, which already handle that provenance (see
chatfs.provider.aistudio.layout).
"""
from chatfs import json as chatfs_json
from chatfs.json import JsonObject, JsonValue
from chatfs.paths import demo_root
from chatfs.provider.aistudio.conversation.massage_json import PROMPT, from_message
from chatfs.provider.aistudio.layout import index_item, place_meta
from chatfs.provider.aistudio.types import Conversation, is_conversation

OUT_DIR = demo_root("aistudio")


def massage_entry(entry: JsonValue) -> Conversation:
    """Project one ListPrompts entry through the shared PROMPT schema.

    Mirrors chatfs.provider.aistudio.conversation.massage_json.massage's
    body, applied directly to an already-unwrapped index entry rather
    than ResolveDriveResource's single-prompt envelope.
    """
    doc: JsonObject = {"prompt": from_message(entry, PROMPT)}
    assert is_conversation(doc), doc
    return doc


def main() -> None:
    import sys

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    dups = 0
    for line in sys.stdin:
        entry = chatfs_json.loads(line)
        item = index_item(massage_entry(entry))
        if item["id"] in seen:
            dups += 1
        seen.add(item["id"])
        _ = place_meta(item, OUT_DIR)
    print(
        f"placed {len(seen)} item(s) under {OUT_DIR} "
        + f"({dups} duplicate-id re-writes)",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
