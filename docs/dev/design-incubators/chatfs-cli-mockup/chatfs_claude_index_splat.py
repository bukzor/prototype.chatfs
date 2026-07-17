#!/usr/bin/env python3
"""Splat claude index pages into per-chat storage.

Reads pages on stdin (one `{data: [...], has_more}` object per line; the
output of `chatfs_claude_index_pluck.jq`). For each item, calls
place_meta which:

    - writes $root/.data/$UUID/meta.json
    - purges existing view symlinks for $UUID
    - creates a view dir-symlink under $root/YYYY/MM/DD/HH:MM:SS±HH:MM/

Pages overlap (the SPA re-fetches stable pages as the user scrolls), so
duplicate uuids across pages are expected; last-write-wins.
"""
import sys
from pathlib import Path

import chatfs_json
from chatfs_claude_layout import place_meta
from chatfs_claude_types import is_index_page

OUT_DIR = Path(__file__).parent / "chatfs.demo" / "claude"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    dups = 0
    for line in sys.stdin:
        page = chatfs_json.loads(line)
        assert is_index_page(page), page
        for item in page["data"]:
            uuid = item["uuid"]
            if uuid in seen:
                dups += 1
            seen.add(uuid)
            _ = place_meta(item, OUT_DIR)
    print(
        f"placed {len(seen)} item(s) under {OUT_DIR} "
        + f"({dups} duplicate-uuid re-writes across pages)",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
