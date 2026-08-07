#!/usr/bin/env python3
"""Capture a chatgpt.com conversation by URL.

Usage:
    python -m chatfs.provider.chatgpt.conversation.url_browse <chatgpt-url>

Assumes (per browse-incidental-capture.md) that visiting `/c/$UUID` also
fires `/backend-api/conversations` for the sidebar, so one browse trip
captures both the conversation document and an index page that mentions
this UUID.

If that assumption is ever violated, `find_index_item` fails loudly and
the recovery path is two-step: index browse → index splat → path_browse.

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
    3. index pluck → .data/$UUID/cdp.jsonl.d/index-pages.jsonl; filter to
       .id == $UUID → meta (fail loudly if absent)
    4. cross-check conversation doc vs index item, null-tolerant
    5. place_meta (writes meta.json, purges + places view dir-symlink)
    6. delegate to path_render

Captures are written directly into `.data/$UUID/` — no temp staging
(matches claude's `capture()` policy). If a later step fails, the
captures remain there for inspection.
"""
from pathlib import Path

from chatfs import json as chatfs_json
from chatfs.json import JsonObject
from chatfs.layout import chat_dir_for
from chatfs.paths import INCUBATOR_ROOT, demo_root
from chatfs.provider.chatgpt import layout as chatgpt_layout
from chatfs.provider.chatgpt.pluck import pluck_index_pages
from chatfs.provider.chatgpt.types import IndexItem, is_index_page
from chatfs.shell import sh as chatfs_sh
from chatfs.shell.capture import pluck
from chatfs.url_browse import null_tolerant_mismatches

ROOT = demo_root("chatgpt")


def find_index_item(data_dir: Path, uuid: str) -> IndexItem:
    """Pluck index pages from CDP into cdp.jsonl.d/index-pages.jsonl;
    return the item matching uuid.

    A cross-check dump, not a contract file — scratch reserved under
    `cdp.jsonl`'s `.d/` sibling per `path-ownership.md`. Fails loudly if
    no sidebar page included this conversation — the user's recovery is
    to run `index browse` then `conversation path browse` against the
    resulting chat dir.
    """
    index_pages = data_dir / "cdp.jsonl.d" / "index-pages.jsonl"
    pluck(pluck_index_pages, data_dir / "cdp.jsonl", index_pages)
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
        f"run index browse | index splat, then use path_browse"
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
        "create_time": chatgpt_layout.created_at(create_time).isoformat(),
    }


def main() -> None:
    import sys

    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <chatgpt-url>", file=sys.stderr)
        sys.exit(2)

    url = sys.argv[1]
    uuid = chatgpt_layout.uuid_from_url(url)

    chat_dir = chat_dir_for(uuid, ROOT)
    data_dir = chatgpt_layout.capture(url, chat_dir)
    conversation = data_dir / "conversation.json"

    item = find_index_item(data_dir, uuid)

    conv_doc = chatfs_json.loads(conversation.read_text())
    assert isinstance(conv_doc, dict), conv_doc
    projected = _index_shaped(conv_doc)
    item_normalized: JsonObject = {
        "id": item["id"],
        "title": item["title"],
        "create_time": chatgpt_layout.created_at(item["create_time"]).isoformat(),
    }
    mismatches = null_tolerant_mismatches(projected, item_normalized)
    assert not mismatches, (
        f"meta fields disagree across conversation and index endpoints "
        f"for {uuid}: {mismatches}"
    )

    _ = chatgpt_layout.place_meta(item, ROOT)

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
