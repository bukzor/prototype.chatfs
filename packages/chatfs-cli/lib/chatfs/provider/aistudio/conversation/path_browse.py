#!/usr/bin/env python3
"""Capture an AI Studio prompt by chat-dir address.

Usage:
    python -m chatfs.provider.aistudio.conversation.path_browse <path-to-chat-dir-or-inside>

The argument resolves to a `.chat/$id/` directory (see
chatfs.shell.place.resolve_chat_dir; need not exist yet). Its
`.data/$id/meta.json` twin must already exist (placed by a prior url
browse).

Steps:
    1. browse $url → .data/$id/cdp.jsonl
    2. pluck cdp.jsonl → .data/$id/conversation.json.d/raw.json
    3. massage → .data/$id/conversation.json
    4. delegate to path_render
"""
from chatfs import json as chatfs_json
from chatfs.layout import data_dir_of
from chatfs.paths import INCUBATOR_ROOT
from chatfs.provider.aistudio import layout as aistudio_layout
from chatfs.provider.aistudio.types import is_index_item
from chatfs.shell import sh as chatfs_sh
from chatfs.shell.capture import run_module
from chatfs.shell.place import resolve_chat_dir


def main() -> None:
    import sys

    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path-to-chat-dir-or-inside>", file=sys.stderr)
        sys.exit(2)

    chat_dir = resolve_chat_dir(sys.argv[1])
    meta = chatfs_json.loads((data_dir_of(chat_dir) / "meta.json").read_text())
    assert is_index_item(meta), meta
    url = aistudio_layout.url_for(meta["id"])

    data_dir = aistudio_layout.capture(url, chat_dir)
    raw = data_dir / "conversation.json.d" / "raw.json"
    run_module(
        "chatfs.provider.aistudio.conversation.massage_json",
        raw,
        data_dir / "conversation.json",
        cwd=INCUBATOR_ROOT,
    )

    _ = chatfs_sh.run(
        [
            sys.executable,
            "-m",
            "chatfs.provider.aistudio.conversation.path_render",
            str(chat_dir),
        ],
        cwd=INCUBATOR_ROOT,
    )


if __name__ == "__main__":
    main()
