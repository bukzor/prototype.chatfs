#!/usr/bin/env python3
"""Splat chatgpt index pages into per-chat storage.

Reads chatgpt.index.jsonl on stdin (one page per line, each
`{items: [...], total, ...}`). For each item, calls place_meta which:

    - writes $root/.chat/$UUID/meta.json
    - purges existing view symlinks for $UUID
    - creates view symlinks under $root/YYYY/MM/DD/HH:MM:SS±HH:MM/
"""
import sys
from pathlib import Path

import chatfs_json
from chatfs_chatgpt_layout import place_meta
from chatfs_chatgpt_types import is_index_page

OUT_DIR = Path(__file__).parent / "chatfs.demo" / "chatgpt"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    for line in sys.stdin:
        page = chatfs_json.loads(line)
        assert is_index_page(page), page
        for item in page["items"]:
            uuid = item["id"]
            assert uuid not in seen, f"duplicate UUID across index pages: {uuid}"
            seen.add(uuid)
            _ = place_meta(item, OUT_DIR)
    print(f"placed {len(seen)} item(s) under {OUT_DIR}", file=sys.stderr)


if __name__ == "__main__":
    main()
