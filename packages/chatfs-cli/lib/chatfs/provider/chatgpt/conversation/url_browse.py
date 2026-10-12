#!/usr/bin/env python3
"""Capture a chatgpt.com conversation by URL.

Usage:
    chatfs-provider-chatgpt-conversation-url-browse --cache <dir> <chatgpt-url>

Visiting `/c/$UUID` also fires `/backend-api/conversations` for the
sidebar's first page -- the 28 most recently updated chats -- so a
recent chat's index item comes along with the browse. The meta.json
placed is the one already on disk, else that sidebar item; with
neither, or with the two disagreeing, this fails (UserError). See
browse-incidental-capture.md, "Which meta.json wins".

When the sidebar has the chat, a second cross-check asserts that the
identity fields agree across the two endpoints (null-tolerant) —
catches schema drift if either side ever changes shape. Unlike claude,
where the conversation doc and index item share literal key names and
representations, chatgpt's conversation doc names the id field
`conversation_id` (not `id`) and carries `create_time` as a unix float
where the index returns an ISO string — `_index_shaped` normalizes
both before the diff so the check stays meaningful instead of
null-tolerance silently skipping every field.

Steps:
    1. browse $url → .data/$UUID/cdp.jsonl
    2. conversation pluck → .data/$UUID/conversation.json.d/raw.jsonl
    3. assemble → .data/$UUID/conversation.json
    4. index pluck → .data/$UUID/cdp.jsonl.d/index-pages.jsonl; filter to
       .id == $UUID → the sidebar's item, if any
    5. cross-check conversation doc vs sidebar item, null-tolerant
    6. choose meta: on disk, else sidebar (UserError if neither, or if
       they disagree)
    7. place_meta (writes meta.json, purges + places view dir-symlink)
    8. delegate to path_render

Captures are written directly into `.data/$UUID/` — no temp staging
(matches claude's `capture()` policy). If a later step fails, the
captures remain there for inspection.
"""
from pathlib import Path

import typed_json
from typed_json import JsonObject
from chatfs.cli import extract_cache
from chatfs.layout import chat_dir_for
from chatfs.provider.chatgpt import layout as chatgpt_layout
from chatfs.provider.chatgpt.pluck import pluck_index_pages
from chatfs.provider.chatgpt.types import IndexItem, is_index_item, is_index_page
from chatfs.shell import sh as chatfs_sh
from chatfs.shell.capture import pluck
from chatfs.url_browse import choose_meta, null_tolerant_mismatches
from chatfs.parsing import parsing
from chatfs.user_error import reports_user_errors


def find_index_item(data_dir: Path, uuid: str) -> IndexItem | None:
    """Pluck index pages from CDP into cdp.jsonl.d/index-pages.jsonl;
    return the item matching uuid, or None if no sidebar page included it.

    A cross-check dump, not a contract file — scratch reserved under
    `cdp.jsonl`'s `.d/` sibling per `path-ownership.md`.
    """
    index_pages = data_dir / "cdp.jsonl.d" / "index-pages.jsonl"
    pluck(pluck_index_pages, data_dir / "cdp.jsonl", index_pages)
    matches: list[IndexItem] = []
    for line in index_pages.read_text().splitlines():
        if not line.strip():
            continue
        with parsing(index_pages):
            page = typed_json.loads(line)
        assert is_index_page(page), page
        for item in page["items"]:
            if item["id"] == uuid:
                matches.append(item)
    assert all(m == matches[0] for m in matches), (
        f"index endpoint returned divergent items for {uuid}: {matches}"
    )
    return matches[0] if matches else None


def read_meta(data_dir: Path) -> IndexItem | None:
    """The meta.json already in `data_dir`, or None if there is none."""
    path = data_dir / "meta.json"
    if not path.exists():
        return None
    with parsing(path):
        meta = typed_json.loads(path.read_text())
    assert is_index_item(meta), meta
    return meta


def _identity(item: IndexItem) -> JsonObject:
    """An index item's identity fields, `create_time` normalized to the
    same ISO 8601 spelling `_index_shaped` gives the conversation doc."""
    return {
        "id": item["id"],
        "title": item["title"],
        "create_time": chatgpt_layout.created_at(item["create_time"]).isoformat(),
    }


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


@reports_user_errors
def main() -> None:
    import os
    import sys

    root, rest = extract_cache(sys.argv[1:], os.environ, chatgpt_layout.PROVIDER)
    if root is None or len(rest) != 1:
        print(f"usage: {sys.argv[0]} --cache <dir> <chatgpt-url>", file=sys.stderr)
        sys.exit(2)
    (url,) = rest

    uuid = chatgpt_layout.uuid_from_url(url)

    chat_dir = chat_dir_for(uuid, root)
    data_dir = chatgpt_layout.capture(url, chat_dir)
    conversation = chatgpt_layout.assemble_conversation(data_dir)

    item = find_index_item(data_dir, uuid)

    if item is not None:
        with parsing(conversation):
            conv_doc = typed_json.loads(conversation.read_text())
        assert isinstance(conv_doc, dict), conv_doc
        mismatches = null_tolerant_mismatches(_index_shaped(conv_doc), _identity(item))
        assert not mismatches, (
            f"meta fields disagree across conversation and index endpoints "
            f"for {uuid}: {mismatches}"
        )

    meta = choose_meta(
        uuid, read_meta(data_dir), item, _identity, chatgpt_layout.PROVIDER
    )
    _ = chatgpt_layout.place_meta(meta, root)

    _ = chatfs_sh.run(
        [
            sys.executable,
            "-m",
            "chatfs.provider.chatgpt.conversation.path_render",
            str(chat_dir),
        ],
    )


if __name__ == "__main__":
    main()
