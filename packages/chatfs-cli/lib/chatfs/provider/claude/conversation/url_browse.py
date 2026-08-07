#!/usr/bin/env python3
"""Capture a claude.ai conversation by URL.

Usage:
    python -m chatfs.provider.claude.conversation.url_browse <claude-url>

Assumes (per browse-incidental-capture.md) that visiting `/chat/$UUID`
also fires `/chat_conversations_v2` for the sidebar, so one browse trip
captures both the conversation document and an index page that mentions
this UUID.

If that assumption is ever violated, `find_index_item` fails loudly and
the recovery path is two-step: index browse → index splat → path_browse.

A second cross-check asserts that the meta-shaped fields agree across
the two endpoints (null-tolerant) — catches schema drift if either side
ever changes shape.

Steps:
    1. browse $url → .data/$UUID/cdp.jsonl
    2. conversation pluck → .data/$UUID/conversation.json
    3. index pluck → .data/$UUID/cdp.jsonl.d/index-pages.jsonl; filter to
       .uuid == $UUID → meta (fail loudly if absent)
    4. cross-check conversation doc vs index item, null-tolerant
    5. place_meta (writes meta.json, purges + places view dir-symlink)
    6. delegate to path_render

Captures are written directly into `.data/$UUID/` — no temp staging.
If a later step fails, the captures remain there for inspection.
Recovery from the long-tail "sidebar didn't include this uuid" case is
to run index browse | index splat (deposits meta.json into the same
`.data/$UUID/`) and then path_render on the chat dir (reuses the
already-captured cdp.jsonl + conversation.json).
"""
from pathlib import Path
from typing import cast

from chatfs import json as chatfs_json
from chatfs.json import JsonObject
from chatfs.layout import chat_dir_for
from chatfs.paths import INCUBATOR_ROOT, demo_root
from chatfs.provider.claude import layout as claude_layout
from chatfs.provider.claude.pluck import pluck_conversation, pluck_index_pages
from chatfs.provider.claude.types import IndexItem, is_index_page
from chatfs.shell import sh as chatfs_sh
from chatfs.shell.capture import capture, pluck
from chatfs.shell.place import place_meta
from chatfs.url_browse import null_tolerant_mismatches

ROOT = demo_root("claude")


def find_index_item(data_dir: Path, uuid: str) -> IndexItem:
    """Pluck index pages from CDP into cdp.jsonl.d/index-pages.jsonl;
    return the item matching uuid.

    A cross-check dump, not a contract file — scratch reserved under
    `cdp.jsonl`'s `.d/` sibling per `path-ownership.md`. Fails loudly if
    no incidentally-captured index page mentioned this uuid — recovery is
    the two-step (index_browse → index_splat → path_browse).
    """
    index_pages = data_dir / "cdp.jsonl.d" / "index-pages.jsonl"
    pluck(pluck_index_pages, data_dir / "cdp.jsonl", index_pages)
    matches: list[IndexItem] = []
    for line in index_pages.read_text().splitlines():
        if not line.strip():
            continue
        page = chatfs_json.loads(line)
        assert is_index_page(page), page
        matches.extend(item for item in page["data"] if item["uuid"] == uuid)
    assert matches, (
        f"no sidebar index page included {uuid}; "
        f"run index browse | index splat, then use path_browse"
    )
    assert all(
        m == matches[0] for m in matches
    ), f"index endpoint returned divergent items for {uuid}: {matches}"
    return matches[0]


def main() -> None:
    import sys

    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <claude-url>", file=sys.stderr)
        sys.exit(2)

    url = sys.argv[1]
    uuid = claude_layout.uuid_from_url(url)

    chat_dir = chat_dir_for(uuid, ROOT)
    data_dir = capture(url, chat_dir, pluck_conversation)
    conversation = data_dir / "conversation.json"

    item = find_index_item(data_dir, uuid)

    conv_doc = chatfs_json.loads(conversation.read_text())
    assert isinstance(conv_doc, dict), conv_doc
    # IndexItem's fields are all str, so this is a safe reinterpretation, not an
    # unverified cast — TypedDict's synthesized Mapping view widens values to
    # `object`, which null_tolerant_mismatches can't recurse into.
    mismatches = null_tolerant_mismatches(conv_doc, cast(JsonObject, dict(item)))
    assert not mismatches, (
        f"meta fields disagree across conversation and index endpoints "
        f"for {uuid}: {mismatches}"
    )

    _ = place_meta(
        item["uuid"], item["name"], claude_layout.created_at(item["created_at"]), item, ROOT
    )

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
