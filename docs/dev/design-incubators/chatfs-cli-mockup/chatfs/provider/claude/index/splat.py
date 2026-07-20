#!/usr/bin/env python3
"""Splat claude index pages into per-chat storage.

Reads pages on stdin (one `{data: [...], has_more}` object per line; the
output of `chatfs.provider.claude.pluck.pluck_index_pages`). For each
item, calls place_meta which:

    - writes $root/.data/$UUID/meta.json
    - purges existing view symlinks for $UUID
    - creates a view dir-symlink under $root/YYYY/MM/DD/HH:MM:SS±HH:MM/

Pages overlap (the SPA re-fetches stable pages as the user scrolls), so
duplicate uuids across pages are expected; last-write-wins.
"""
from chatfs import json as chatfs_json
from chatfs.paths import demo_root
from chatfs.provider.claude import layout as claude_layout
from chatfs.provider.claude.types import is_index_page
from chatfs.shell.place import place_meta

OUT_DIR = demo_root("claude")


def main() -> None:
    import sys

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
            _ = place_meta(
                item["uuid"],
                item["name"],
                claude_layout.created_at(item["created_at"]),
                item,
                OUT_DIR,
            )
    print(
        f"placed {len(seen)} item(s) under {OUT_DIR} "
        + f"({dups} duplicate-uuid re-writes across pages)",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
