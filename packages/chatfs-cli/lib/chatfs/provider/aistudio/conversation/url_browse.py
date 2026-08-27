#!/usr/bin/env python3
"""Capture an aistudio.google.com prompt by URL.

Usage:
    chatfs-aistudio-conversation-url-browse --cache <dir> <aistudio-url>

Unlike chatgpt/claude, there's no separate index endpoint to derive
meta.json from yet (ListPrompts hasn't been reverse-engineered — see
.claude/todo.kb/2026-06-20-000-aistudio-provider-parity-ladder.md). AI
Studio's single ResolveDriveResource RPC carries both identity
(name/title/created, via chatfs.provider.aistudio.layout.index_item)
and turn content in the same body, so there's no incidental-capture
cross-check to do here (contrast chatgpt/claude's find_index_item):
place_meta derives straight from the same capture that becomes
conversation.json.

Steps:
    1. browse $url -> .data/$id/cdp.jsonl
    2. conversation pluck -> .data/$id/conversation.json.d/raw.json (raw JSPB array)
    3. massage -> .data/$id/conversation.json (named, matches chatgpt/claude shape)
    4. place_meta from the raw doc (writes meta.json, view dir-symlink)
    5. delegate to path_render
"""
import typed_json
from chatfs.cli import extract_cache
from chatfs.layout import chat_dir_for
from chatfs.provider.aistudio import layout as aistudio_layout
from chatfs.provider.aistudio.types import is_conversation
from chatfs.shell import sh as chatfs_sh
from chatfs.shell.capture import run_module


def main() -> None:
    import os
    import sys

    root, rest = extract_cache(sys.argv[1:], os.environ)
    if root is None or len(rest) != 1:
        print(f"usage: {sys.argv[0]} --cache <dir> <aistudio-url>", file=sys.stderr)
        sys.exit(2)
    (url,) = rest

    id_ = aistudio_layout.uuid_from_url(url)

    chat_dir = chat_dir_for(id_, root)
    data_dir = aistudio_layout.capture(url, chat_dir)
    raw = data_dir / "conversation.json.d" / "raw.json"
    conversation = data_dir / "conversation.json"

    chatfs_sh.log(f"Massaging {raw} → {conversation} ...")
    run_module(
        "chatfs.provider.aistudio.conversation.massage_json",
        raw,
        conversation,
    )

    parsed = typed_json.loads(conversation.read_text())
    assert is_conversation(parsed), parsed
    item = aistudio_layout.index_item(parsed)
    assert item["id"] == id_, (item["id"], id_)
    chat_dir = aistudio_layout.place_meta(item, root).chat_dir

    _ = chatfs_sh.run(
        [
            sys.executable,
            "-m",
            "chatfs.provider.aistudio.conversation.path_render",
            str(chat_dir),
        ],
    )


if __name__ == "__main__":
    main()
