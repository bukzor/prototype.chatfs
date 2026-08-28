#!/usr/bin/env python3
"""Splat AI Studio ListPrompts index entries into per-chat storage.

Usage:
    chatfs-aistudio-index-splat --cache <dir>

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

stdout: one placement record per chat placed (jsonl) --
`{id, title, chat_dir, view}`, the shared shape every provider's index
splat emits. Deduplicated: a uuid already placed this run
is re-written but not re-announced, so the line count matches the
"placed N item(s)" summary. Feed it to whatever acts on a fresh
index -- `jq -r .chat_dir | xargs -rL1 chatfs-aistudio-conversation-path-browse`.
"""
import json

import typed_json
from typed_json import JsonObject, JsonValue
from chatfs.cli import extract_cache
from chatfs.provider.aistudio.conversation.massage_json import PROMPT, from_message
from chatfs.provider.aistudio.layout import PROVIDER, index_item, place_meta
from chatfs.provider.aistudio.types import Conversation, is_conversation
from chatfs.shell import sh as chatfs_sh


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
    import os
    import sys

    root, rest = extract_cache(sys.argv[1:], os.environ, PROVIDER)
    if root is None or rest:
        print(f"usage: {sys.argv[0]} --cache <dir>", file=sys.stderr)
        sys.exit(2)

    root.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    dups = 0
    for line in sys.stdin:
        entry = typed_json.loads(line)
        item = index_item(massage_entry(entry))
        placed = place_meta(item, root)
        if item["id"] in seen:
            dups += 1
        else:
            print(json.dumps(placed.record()))
        seen.add(item["id"])
    chatfs_sh.log(
        f"placed {len(seen)} item(s) under {root} " + f"({dups} duplicate-id re-writes)"
    )


if __name__ == "__main__":
    main()
