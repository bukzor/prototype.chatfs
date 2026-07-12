#!/usr/bin/env python3
"""Capture an AI Studio prompt by chat-dir address.

Usage:
    chatfs_aistudio_conversation_path_browse.py <path-to-chat-dir-or-inside>

The argument resolves to a `.chat/$id/` directory (see
chatfs_aistudio_layout.resolve_chat_dir). `.data/meta.json` must already
live there (placed by a prior url browse).

Steps:
    1. browse $url → .data/cdp.jsonl
    2. pluck cdp.jsonl → .data/conversation.raw.json
    3. massage → .data/conversation.json
    4. delegate to chatfs_aistudio_conversation_path_render.py
"""
import subprocess
import sys
from pathlib import Path

import chatfs_json
from chatfs_aistudio_layout import DATA_DIR_NAME, capture, resolve_chat_dir
from chatfs_aistudio_types import is_index_item
from chatfs_layout import run_pluck

HERE = Path(__file__).parent
MASSAGE_JSON = HERE / "chatfs_aistudio_conversation_massage_json.py"
PATH_RENDER = HERE / "chatfs_aistudio_conversation_path_render.py"


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path-to-chat-dir-or-inside>", file=sys.stderr)
        sys.exit(2)

    chat_dir = resolve_chat_dir(sys.argv[1])
    meta = chatfs_json.loads((chat_dir / DATA_DIR_NAME / "meta.json").read_text())
    assert is_index_item(meta), meta
    url = f"https://aistudio.google.com/prompts/{meta['id']}"

    data_dir = capture(url, chat_dir)
    run_pluck(MASSAGE_JSON, data_dir / "conversation.raw.json", data_dir / "conversation.json")

    _ = subprocess.run([str(PATH_RENDER), str(chat_dir)], check=True)


if __name__ == "__main__":
    main()
