#!/usr/bin/env python3
"""Capture a chatgpt.com conversation by chat-dir address.

Usage:
    chatfs_chatgpt_conversation_path_browse.py <path-to-chat-dir-or-inside>

The argument resolves to a `.chat/$UUID/` directory (see
chatfs_chatgpt_layout.resolve_chat_dir). `.data/meta.json` must already
live there (placed by index splat or url browse).

Steps:
    1. browse $url → .data/cdp.jsonl
    2. pluck cdp.jsonl → .data/conversation.json
    3. delegate to chatfs_chatgpt_conversation_path_render.py
"""
import subprocess
import sys
from pathlib import Path

import chatfs_json
from chatfs_chatgpt_layout import DATA_DIR_NAME, resolve_chat_dir
from chatfs_chatgpt_types import is_index_item

HERE = Path(__file__).parent
PLUCK = HERE / "chatfs_chatgpt_conversation_pluck.jq"
PATH_RENDER = HERE / "chatfs_chatgpt_conversation_path_render.py"


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path-to-chat-dir-or-inside>", file=sys.stderr)
        sys.exit(2)

    chat_dir = resolve_chat_dir(sys.argv[1])
    data_dir = chat_dir / DATA_DIR_NAME

    meta = chatfs_json.loads((data_dir / "meta.json").read_text())
    assert is_index_item(meta), meta
    url = f"https://chatgpt.com/c/{meta['id']}"
    cdp = data_dir / "cdp.jsonl"
    conversation = data_dir / "conversation.json"

    cdp.unlink(missing_ok=True)
    conversation.unlink(missing_ok=True)

    print(f"Capturing {url} → {cdp} ...", file=sys.stderr)
    with cdp.open("wb") as f:
        _ = subprocess.run(["har-browse", url], stdout=f, check=True)

    print(f"Plucking conversation → {conversation} ...", file=sys.stderr)
    with cdp.open("rb") as src, conversation.open("wb") as dst:
        _ = subprocess.run([str(PLUCK)], stdin=src, stdout=dst, check=True)

    _ = subprocess.run([str(PATH_RENDER), str(chat_dir)], check=True)


if __name__ == "__main__":
    main()
