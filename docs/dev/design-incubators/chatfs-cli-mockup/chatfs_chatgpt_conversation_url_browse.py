#!/usr/bin/env python3
"""Capture a chatgpt.com conversation by URL.

Usage:
    chatfs_chatgpt_conversation_url_browse.py <chatgpt-url>

Assumes (per browse-incidental-capture.md) that visiting `/c/$UUID` also
fires `/backend-api/conversations` for the sidebar, so one browse trip
captures both the conversation document and an index page that mentions
this UUID.

If that assumption is ever violated, `find_index_item` fails loudly and
the recovery path is two-step: `chatfs_chatgpt_index_browse.sh` →
`chatfs_chatgpt_index_splat.py` → `chatfs_chatgpt_conversation_path_browse.py`.

A second cross-check asserts that the identity fields agree across the
two endpoints (null-tolerant) — catches schema drift if either side
ever changes shape. Unlike claude, where the conversation doc and index
item share literal key names and representations, chatgpt's
conversation doc names the id field `conversation_id` (not `id`) and
carries `create_time` as a unix float where the index returns an ISO
string — `_index_shaped` normalizes both before the diff so the check
stays meaningful instead of null-tolerance silently skipping every
field.

Steps:
    1. browse $url → .data/$UUID/cdp.jsonl
    2. conversation pluck → .data/$UUID/conversation.json
    3. index pluck → .data/$UUID/index-pages.jsonl; filter to
       .id == $UUID → meta (fail loudly if absent)
    4. cross-check conversation doc vs index item, null-tolerant
    5. place_meta (writes meta.json, purges + places view dir-symlink)
    6. delegate to path_render

Captures are written directly into `.data/$UUID/` — no temp staging
(matches claude's `capture()` policy). If a later step fails, the
captures remain there for inspection.
"""
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import chatfs_json
from chatfs_chatgpt_layout import capture, chat_dir_for, created_at, place_meta
from chatfs_chatgpt_types import IndexItem, is_index_page
from chatfs_json import JsonObject
from chatfs_layout import run_pluck
from chatfs_url_browse import null_tolerant_mismatches

HERE = Path(__file__).parent
INDEX_PLUCK = HERE / "chatfs_chatgpt_index_pluck.jq"
PATH_RENDER = HERE / "chatfs_chatgpt_conversation_path_render.py"
ROOT = HERE / "chatfs.demo" / "chatgpt"


def uuid_from_url(url: str) -> str:
    parts = urlparse(url).path.strip("/").split("/")
    assert len(parts) == 2 and parts[0] == "c", url
    return parts[1]


def find_index_item(data_dir: Path, uuid: str) -> IndexItem:
    """Pluck index pages from CDP into index-pages.jsonl; return the item
    matching uuid.

    Fails loudly if no sidebar page included this conversation — the
    user's recovery is to run `index browse` then `conversation path
    browse` against the resulting chat dir.
    """
    index_pages = data_dir / "index-pages.jsonl"
    run_pluck(INDEX_PLUCK, data_dir / "cdp.jsonl", index_pages)
    matches: list[IndexItem] = []
    for line in index_pages.read_text().splitlines():
        if not line.strip():
            continue
        page = chatfs_json.loads(line)
        assert is_index_page(page), page
        for item in page["items"]:
            if item["id"] == uuid:
                matches.append(item)
    assert matches, (
        f"no sidebar index page included {uuid}; "
        f"run `chatfs_chatgpt_index_browse.sh` and use `conversation_path_browse.py`"
    )
    assert all(m == matches[0] for m in matches), (
        f"index endpoint returned divergent items for {uuid}: {matches}"
    )
    return matches[0]


def _index_shaped(conv_doc: JsonObject) -> JsonObject:
    """Project the conversation doc's identity fields into IndexItem shape.

    `conversation_id` -> `id`; `create_time` reparsed to ISO 8601 so it
    compares equal to the index endpoint's string, regardless of which
    side's representation the doc happens to carry.
    """
    create_time = conv_doc["create_time"]
    assert isinstance(create_time, (int, float, str)), create_time
    return {
        "id": conv_doc["conversation_id"],
        "title": conv_doc["title"],
        "create_time": created_at(create_time).isoformat(),
    }


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <chatgpt-url>", file=sys.stderr)
        sys.exit(2)

    url = sys.argv[1]
    uuid = uuid_from_url(url)

    chat_dir = chat_dir_for(uuid, ROOT)
    data_dir = capture(url, chat_dir)
    conversation = data_dir / "conversation.json"

    item = find_index_item(data_dir, uuid)

    conv_doc = chatfs_json.loads(conversation.read_text())
    assert isinstance(conv_doc, dict), conv_doc
    projected = _index_shaped(conv_doc)
    item_normalized: JsonObject = {
        "id": item["id"],
        "title": item["title"],
        "create_time": created_at(item["create_time"]).isoformat(),
    }
    mismatches = null_tolerant_mismatches(projected, item_normalized)
    assert not mismatches, (
        f"meta fields disagree across conversation and index endpoints "
        f"for {uuid}: {mismatches}"
    )

    _ = place_meta(item, ROOT)

    _ = subprocess.run([str(PATH_RENDER), str(chat_dir)], check=True)


if __name__ == "__main__":
    main()
