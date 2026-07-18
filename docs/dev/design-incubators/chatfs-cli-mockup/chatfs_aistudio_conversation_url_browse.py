#!/usr/bin/env python3
"""Capture an aistudio.google.com prompt by URL.

Usage:
    chatfs_aistudio_conversation_url_browse.py <aistudio-url>

Unlike chatgpt/claude, there's no separate index endpoint to derive
meta.json from yet (ListPrompts hasn't been reverse-engineered — see
.claude/todo.kb/2026-06-20-000-aistudio-provider-parity-ladder.md). AI
Studio's single ResolveDriveResource RPC carries both identity
(name/title/created, via chatfs_aistudio_layout.index_item) and turn
content in the same body, so there's no incidental-capture cross-check
to do here (contrast chatgpt/claude's find_index_item): place_meta
derives straight from the same capture that becomes conversation.json.

Steps:
    1. browse $url -> .data/$id/cdp.jsonl
    2. conversation pluck -> .data/$id/conversation.raw.json (raw JSPB array)
    3. massage -> .data/$id/conversation.json (named, matches chatgpt/claude shape)
    4. place_meta from the raw doc (writes meta.json, view dir-symlink)
    5. delegate to path_render
"""
import sys
from pathlib import Path
from urllib.parse import urlparse

import chatfs_json
import chatfs_sh
from chatfs_aistudio_layout import capture, chat_dir_for, index_item, place_meta
from chatfs_aistudio_types import is_conversation
from chatfs_layout import run_pluck

HERE = Path(__file__).parent
MASSAGE_JSON = HERE / "chatfs_aistudio_conversation_massage_json.py"
PATH_RENDER = HERE / "chatfs_aistudio_conversation_path_render.py"
ROOT = HERE / "chatfs.demo" / "aistudio"


def id_from_url(url: str) -> str:
    parts = urlparse(url).path.strip("/").split("/")
    assert len(parts) == 2 and parts[0] == "prompts", url
    return parts[1]


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <aistudio-url>", file=sys.stderr)
        sys.exit(2)

    url = sys.argv[1]
    id_ = id_from_url(url)

    chat_dir = chat_dir_for(id_, ROOT)
    data_dir = capture(url, chat_dir)
    raw = data_dir / "conversation.raw.json"
    conversation = data_dir / "conversation.json"

    print(f"Massaging {raw} → {conversation} ...", file=sys.stderr)
    run_pluck(MASSAGE_JSON, raw, conversation)

    parsed = chatfs_json.loads(conversation.read_text())
    assert is_conversation(parsed), parsed
    item = index_item(parsed)
    assert item["id"] == id_, (item["id"], id_)
    chat_dir = place_meta(item, ROOT)

    _ = chatfs_sh.run([str(PATH_RENDER), str(chat_dir)])


if __name__ == "__main__":
    main()
