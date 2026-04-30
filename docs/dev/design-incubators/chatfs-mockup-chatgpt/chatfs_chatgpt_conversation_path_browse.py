#!/usr/bin/env python3
"""Capture a chatgpt.com conversation page.

Usage:
    chatfs_chatgpt_conversation_path_browse.py <path-to-page-file>

<path-to-page-file> is anything inside a per-conversation directory
containing meta.json (e.g. the .md placeholder or meta.json itself).
The conversation id is read from meta.json; output is written next to
it as cdp.jsonl.

Steps:
    1. browse $url → cdp.jsonl
    2. pluck cdp.jsonl → $UUID.json
    3. delegate to chatfs_chatgpt_conversation_path_render.py (splat + render)

Pluck is an implementation detail of browse here; iterators that
want to re-render without re-capturing should use path_render directly.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
PLUCK = HERE / "chatfs_chatgpt_conversation_pluck.jq"
PATH_RENDER = HERE / "chatfs_chatgpt_conversation_path_render.py"


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path-to-page-file>", file=sys.stderr)
        sys.exit(2)

    page = Path(sys.argv[1])
    if page.exists(follow_symlinks=False) and not page.is_dir():
        page = page.parent

    meta = json.loads((page / "meta.json").read_text())
    url = f"https://chatgpt.com/c/{meta['id']}"
    cdp = page / "cdp.jsonl"
    conversation = page / f"{meta['id']}.json"

    cdp.unlink(missing_ok=True)
    conversation.unlink(missing_ok=True)

    print(f"Capturing {url} → {cdp} ...", file=sys.stderr)
    with cdp.open("wb") as f:
        subprocess.run(["har-browse", url], stdout=f, check=True)

    print(f"Plucking conversation → {conversation} ...", file=sys.stderr)
    with cdp.open("rb") as src, conversation.open("wb") as dst:
        subprocess.run([str(PLUCK)], stdin=src, stdout=dst, check=True)

    subprocess.run([str(PATH_RENDER), str(page)], check=True)


if __name__ == "__main__":
    main()
