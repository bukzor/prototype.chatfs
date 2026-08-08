#!/usr/bin/env python3
"""Splat chatgpt index pages into per-chat storage.

Reads chatgpt.index.jsonl on stdin (one page per line, each
`{items: [...], total, ...}`). For each item, calls place_meta which:

    - writes $root/.data/$UUID/meta.json
    - purges existing view symlinks for $UUID
    - creates view symlinks under $root/YYYY/MM/DD/HH:MM:SS±HH:MM/
"""
from pathlib import Path

import typed_json
from chatfs.provider.chatgpt.layout import place_meta
from chatfs.provider.chatgpt.types import is_index_page


def main() -> None:
    import sys

    match sys.argv[1:]:
        case ["--cache", cache]:
            root = Path(cache)
        case _:
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
            _ = place_meta(item, root)
    print(f"placed {len(seen)} item(s) under {root}", file=sys.stderr)


if __name__ == "__main__":
    main()
