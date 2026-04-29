#!/usr/bin/env python3
"""Capture a chatgpt.com conversation page.

Usage:
    chatfs_chatgpt_conversation_path_browse.py <path-to-page-file>

<path-to-page-file> is anything inside a per-conversation directory
containing meta.json (e.g. the .md placeholder or meta.json itself).
The conversation id is read from meta.json; output is written next to
it as content.cdp.jsonl.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

MOUNT = Path(__file__).parent / "chatfs.demo"
MAX_AGE_SEC = 1000 * 60 * 60  # XXX: temporarily 1000h


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path-to-page-file>", file=sys.stderr)
        sys.exit(2)

    page = Path(sys.argv[1])
    if page.exists(follow_symlinks=False) and not page.is_dir():
        page = page.parent

    meta = json.loads((page / "meta.json").read_text())
    url = f"https://chatgpt.com/c/{meta['id']}"
    out = page / "content.cdp.jsonl"

    if out.exists() and time.time() - out.stat().st_mtime < MAX_AGE_SEC:
        print(f"{out} is fresh (< {MAX_AGE_SEC // 60}m); skipping capture.", file=sys.stderr)
    else:
        print(f"Capturing {url} → {out} ...", file=sys.stderr)
        with out.open("wb") as f:
            subprocess.run(["har-browse", url], stdout=f, check=True)

    pluck = Path(__file__).parent / "chatfs_chatgpt_conversation_pluck.jq"
    conversation = page / f"{meta['id']}.json"
    print(f"Plucking conversation → {conversation} ...", file=sys.stderr)
    with out.open("rb") as src, conversation.open("wb") as dst:
        subprocess.run([str(pluck)], stdin=src, stdout=dst, check=True)

    print(f"Splatting {conversation} ...", file=sys.stderr)
    subprocess.run(["chatgpt-splat", str(conversation)], check=True)


if __name__ == "__main__":
    main()
