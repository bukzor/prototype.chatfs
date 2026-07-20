#!/usr/bin/env python3
"""Capture a claude.ai conversation by chat-dir address.

Usage:
    python -m chatfs.provider.claude.conversation.path_browse <path-to-chat-dir-or-inside>

The argument resolves to a `.chat/$UUID/` directory (see
chatfs.shell.place.resolve_chat_dir; need not exist yet). Its
`.data/$UUID/meta.json` twin must already exist (placed by index splat
or url browse).

Steps:
    1. browse $url → .data/$UUID/cdp.jsonl
    2. pluck cdp.jsonl → .data/$UUID/conversation.json
    3. delegate to path_render, as a subprocess (see path_render's own
       module docstring for why: the CLI-shaped calling convention stays
       exercised, and subsystem coupling stays scoped to argv/stdio)
"""
from chatfs import json as chatfs_json
from chatfs.layout import data_dir_of
from chatfs.paths import INCUBATOR_ROOT
from chatfs.provider.claude import layout as claude_layout
from chatfs.provider.claude.pluck import pluck_conversation
from chatfs.provider.claude.types import is_index_item
from chatfs.shell import sh as chatfs_sh
from chatfs.shell.capture import capture
from chatfs.shell.place import resolve_chat_dir


def main() -> None:
    import sys

    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path-to-chat-dir-or-inside>", file=sys.stderr)
        sys.exit(2)

    chat_dir = resolve_chat_dir(sys.argv[1])
    meta = chatfs_json.loads((data_dir_of(chat_dir) / "meta.json").read_text())
    assert is_index_item(meta), meta
    url = claude_layout.url_for(meta["uuid"])

    _ = capture(url, chat_dir, pluck_conversation)

    _ = chatfs_sh.run(
        [
            sys.executable,
            "-m",
            "chatfs.provider.claude.conversation.path_render",
            str(chat_dir),
        ],
        cwd=INCUBATOR_ROOT,
    )


if __name__ == "__main__":
    main()
