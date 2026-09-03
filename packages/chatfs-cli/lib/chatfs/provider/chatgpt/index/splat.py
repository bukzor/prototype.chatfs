#!/usr/bin/env python3
"""Splat chatgpt index pages into per-chat storage.

Reads chatgpt.index.jsonl on stdin (one page per line, each
`{items: [...], total, ...}`). For each item, calls place_meta which:

    - writes $root/.data/$UUID/meta.json
    - purges existing view symlinks for $UUID
    - creates view symlinks under $root/YYYY/MM/DD/HH:MM:SS±HH:MM/

stdout: one placement record per chat placed (jsonl) --
`{id, title, chat_dir, view, updated}`, the shared shape every provider's index
splat emits. Deduplicated: a uuid already placed this run
is re-written but not re-announced, so the line count matches the
"placed N item(s)" summary. Feed it to whatever acts on a fresh
index -- `jq -r .chat_dir | xargs -rL1 chatfs-provider-chatgpt-conversation-path-browse`.
"""
import json

import typed_json
from chatfs.cli import extract_cache
from chatfs.provider.chatgpt.layout import PROVIDER, place_meta
from chatfs.provider.chatgpt.types import is_index_page
from chatfs.shell import sh as chatfs_sh


def main() -> None:
    import os
    import sys

    root, rest = extract_cache(sys.argv[1:], os.environ, PROVIDER)
    if root is None or rest:
        print(f"usage: {sys.argv[0]} --cache <dir>", file=sys.stderr)
        sys.exit(2)

    root.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    for line in sys.stdin:
        page = typed_json.loads(line)
        assert is_index_page(page), page
        for item in page["items"]:
            uuid = item["id"]
            assert uuid not in seen, f"duplicate UUID across index pages: {uuid}"
            seen.add(uuid)
            print(json.dumps(place_meta(item, root).record()))
    chatfs_sh.log(f"placed {len(seen)} item(s) under {root}")


if __name__ == "__main__":
    main()
