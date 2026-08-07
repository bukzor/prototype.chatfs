#!/usr/bin/env python3
"""Capture a chatgpt.com conversation by chat-dir address.

Usage:
    python -m chatfs.provider.chatgpt.conversation.path_browse <path-to-chat-dir-or-inside>

The argument resolves to a `.chat/$UUID/` directory (see
chatfs.shell.place.resolve_chat_dir; need not exist yet). Its
`.data/$UUID/meta.json` twin must already exist (placed by index splat
or url browse).

Steps:
    1. browse $url → .data/$UUID/cdp.jsonl
    2. pluck cdp.jsonl → .data/$UUID/conversation.json
    3. delegate to path_render
"""
from chatfs import json as chatfs_json
from chatfs.layout import data_dir_of
from chatfs.paths import INCUBATOR_ROOT
from chatfs.provider.chatgpt import layout as chatgpt_layout
from chatfs.provider.chatgpt.types import is_index_item
from chatfs.shell import sh as chatfs_sh
from chatfs.shell.place import resolve_chat_dir


def main() -> None:
    import sys

    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path-to-chat-dir-or-inside>", file=sys.stderr)
        sys.exit(2)

    chat_dir = resolve_chat_dir(sys.argv[1])
    meta = chatfs_json.loads((data_dir_of(chat_dir) / "meta.json").read_text())
    assert is_index_item(meta), meta
    url = chatgpt_layout.url_for(meta["id"])

    _ = chatgpt_layout.capture(url, chat_dir)

    _ = chatfs_sh.run(
        [
            sys.executable,
            "-m",
            "chatfs.provider.chatgpt.conversation.path_render",
            str(chat_dir),
        ],
        cwd=INCUBATOR_ROOT,
    )


if __name__ == "__main__":
    main()
