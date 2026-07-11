#!/usr/bin/env python3
"""Splat AI Studio ListPrompts index entries into per-chat storage.

Reads one index entry per line on stdin — chatfs_aistudio_index_pluck.jq's
output. Pluck already flattens each response's entry list (`.[0][]`), so
this script never sees a page/envelope shape and doesn't need to know or
care how many ListPrompts responses were captured — one page or many
(pagination), each entry just arrives as its own line.

Each entry is massaged through the same PROMPT schema ResolveDriveResource
uses (verified: entries decode with it unchanged, just with an empty
chunkedPrompt — no turn content on an index-only entry), then handed to
index_item/place_meta, which already handle that provenance (see
chatfs_aistudio_layout.py).
"""
import sys
from pathlib import Path

import chatfs_json
from chatfs_aistudio_conversation_massage_json import PROMPT, from_message
from chatfs_aistudio_layout import index_item, place_meta
from chatfs_aistudio_types import Conversation, is_conversation
from chatfs_json import JsonObject, JsonValue

OUT_DIR = Path(__file__).parent / "chatfs.demo" / "aistudio"


def massage_entry(entry: JsonValue) -> Conversation:
    """Project one ListPrompts entry through the shared PROMPT schema.

    Mirrors chatfs_aistudio_conversation_massage_json.massage's body,
    applied directly to an already-unwrapped index entry rather than
    ResolveDriveResource's single-prompt envelope.
    """
    doc: JsonObject = {"prompt": from_message(entry, PROMPT)}
    assert is_conversation(doc), doc
    return doc


def main() -> None:
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
