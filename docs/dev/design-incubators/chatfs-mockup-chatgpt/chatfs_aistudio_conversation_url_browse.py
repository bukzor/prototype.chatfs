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
    1. browse $url -> .chat/$id/.data/cdp.jsonl
    2. conversation pluck -> .data/conversation.raw.json (raw JSPB array)
    3. massage -> .data/conversation.json (named, matches chatgpt/claude shape)
    4. place_meta from the raw doc (writes meta.json, view dir-symlink)

No delegation to a path_render yet: chatfs_aistudio_conversation_render.py
and chatfs_aistudio_conversation_path_render.py are still unbuilt rungs
(todo.kb). Run chatfs_aistudio_conversation_splat.py by hand for now.
"""
import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

from chatfs_aistudio_layout import chat_dir_for, data_dir_for, index_item, place_meta

HERE = Path(__file__).parent
CONVERSATION_PLUCK = HERE / "chatfs_aistudio_conversation_pluck.jq"
MASSAGE_JSON = HERE / "chatfs_aistudio_conversation_massage_json.py"
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

    data_dir = data_dir_for(id_, ROOT)
    data_dir.mkdir(parents=True, exist_ok=True)
    cdp = data_dir / "cdp.jsonl"
    raw = data_dir / "conversation.raw.json"
    conversation = data_dir / "conversation.json"

    cdp.unlink(missing_ok=True)
    raw.unlink(missing_ok=True)
    conversation.unlink(missing_ok=True)

    print(f"Capturing {url} → {cdp} ...", file=sys.stderr)
    with cdp.open("wb") as f:
        subprocess.run(["har-browse", url], stdout=f, check=True)

    print(f"Plucking conversation → {conversation} ...", file=sys.stderr)
    with cdp.open("rb") as src, raw.open("wb") as dst:
        subprocess.run([str(CONVERSATION_PLUCK)], stdin=src, stdout=dst, check=True)

    with raw.open("rb") as src, conversation.open("wb") as dst:
        subprocess.run([str(MASSAGE_JSON)], stdin=src, stdout=dst, check=True)

    doc = json.loads(conversation.read_text())
    item = index_item(doc)
    assert item["id"] == id_, (item["id"], id_)
    place_meta(item, ROOT)

    print(f"Done: {chat_dir_for(id_, ROOT)}", file=sys.stderr)


if __name__ == "__main__":
    main()
