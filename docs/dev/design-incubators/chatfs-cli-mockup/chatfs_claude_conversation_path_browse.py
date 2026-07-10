#!/usr/bin/env python3
"""Capture a claude.ai conversation by chat-dir address.

Usage:
    chatfs_claude_conversation_path_browse.py <path-to-chat-dir-or-inside>

The argument resolves to a `.chat/$UUID/` directory (see
chatfs_claude_layout.resolve_chat_dir). `.data/meta.json` must already
live there (placed by index splat or url browse).

Steps:
    1. browse $url → .data/cdp.jsonl
    2. pluck cdp.jsonl → .data/conversation.json
    3. delegate to chatfs_claude_conversation_path_render.py
"""
import subprocess
import sys
from pathlib import Path

import chatfs_json
from chatfs_claude_layout import DATA_DIR_NAME, capture, resolve_chat_dir
from chatfs_claude_types import is_index_item

HERE = Path(__file__).parent
PATH_RENDER = HERE / "chatfs_claude_conversation_path_render.py"


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path-to-chat-dir-or-inside>", file=sys.stderr)
        sys.exit(2)

    chat_dir = resolve_chat_dir(sys.argv[1])
    meta = chatfs_json.loads((chat_dir / DATA_DIR_NAME / "meta.json").read_text())
    assert is_index_item(meta), meta
    url = f"https://claude.ai/chat/{meta['uuid']}"

    _ = capture(url, chat_dir)

    _ = subprocess.run([str(PATH_RENDER), str(chat_dir)], check=True)


if __name__ == "__main__":
    main()
