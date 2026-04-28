#!/usr/bin/env python3
"""Splat chatgpt index pages into a date-tree.

Reads chatgpt.index.jsonl on stdin (one page per line, each
`{items: [...], total, ...}`). For each item, writes:

    chatfs.demo/chatgpt/YYYY/MM/DD/HH:MM:SS/meta.json
    chatfs.demo/chatgpt/YYYY/MM/DD/HH:MM:SS/$TITLE.md   # broken self-symlink

The .md is a self-referential symlink: its target is its own basename,
so dereferencing it yields ELOOP. This makes the title visible in
`ls` while signalling "not yet materialized" to consumers.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Mapping

OUT_DIR = Path(__file__).parent / "chatfs.demo" / "chatgpt"


def safe_filename(title: str) -> str:
    return title.replace("/", "∕").replace("\x00", "")


def time_dir(out_dir: Path, create_time: str) -> Path:
    # create_time is ISO 8601 UTC, e.g. "2026-04-15T14:53:42.270850Z"
    dt = datetime.fromisoformat(create_time.replace("Z", "+00:00"))
    return out_dir / f"{dt:%Y/%m/%d/%H:%M:%S}"


def write_item(item: Mapping[str, object], out_dir: Path) -> Path:
    title = item["title"]
    create_time = item["create_time"]
    assert isinstance(title, str), title
    assert isinstance(create_time, str), create_time

    d = time_dir(out_dir, create_time)
    d.mkdir(parents=True, exist_ok=True)

    (d / "meta.json").write_text(json.dumps(item, indent=2) + "\n")

    link_name = safe_filename(title) + ".md"
    link_path = d / link_name
    if link_path.is_symlink() or link_path.exists():
        link_path.unlink()
    os.symlink(link_name, link_path)  # target = own basename → broken self-link

    return d


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    seen: set[Path] = set()
    collisions = 0
    for line in sys.stdin:
        page = json.loads(line)
        for item in page["items"]:
            d = write_item(item, OUT_DIR)
            if d in seen:
                collisions += 1
            seen.add(d)
    print(f"wrote {len(seen)} items under {OUT_DIR}", file=sys.stderr)
    if collisions:
        print(f"warning: {collisions} timestamp collision(s) overwritten", file=sys.stderr)


if __name__ == "__main__":
    main()
