#!/usr/bin/env python3
"""Splat chatgpt index pages into a date-tree.

Reads chatgpt.index.jsonl on stdin (one page per line, each
`{items: [...], total, ...}`). For each item, writes:

    chatfs.demo/chatgpt/YYYY/MM/DD/HH:MM:SS/meta.json
    chatfs.demo/chatgpt/YYYY/MM/DD/HH:MM:SS/$TITLE.md   # broken self-symlink
"""
import json
import sys
from pathlib import Path

from chatfs_chatgpt_layout import place_meta

OUT_DIR = Path(__file__).parent / "chatfs.demo" / "chatgpt"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    seen: set[Path] = set()
    collisions = 0
    for line in sys.stdin:
        page = json.loads(line)
        for item in page["items"]:
            d = place_meta(item, OUT_DIR)
            if d in seen:
                collisions += 1
            seen.add(d)
    print(f"wrote {len(seen)} items under {OUT_DIR}", file=sys.stderr)
    if collisions:
        print(f"warning: {collisions} timestamp collision(s) overwritten", file=sys.stderr)


if __name__ == "__main__":
    main()
