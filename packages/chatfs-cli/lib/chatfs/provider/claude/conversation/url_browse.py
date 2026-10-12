#!/usr/bin/env python3
"""Capture a claude.ai conversation by URL.

Usage:
    chatfs-provider-claude-conversation-url-browse --cache <dir> <claude-url>

Visiting `/chat/$UUID` also fires `/chat_conversations_v2` for the
sidebar, so a recent chat's index item comes along with the browse.
The meta.json placed is the one already on disk, else that sidebar
item; with neither, or with the two disagreeing, this fails
(UserError). See browse-incidental-capture.md, "Which meta.json wins".

When the sidebar has the chat, a second cross-check asserts that the
meta-shaped fields agree across the two endpoints (null-tolerant) —
catches schema drift if either side ever changes shape.

Steps:
    1. browse $url → .data/$UUID/cdp.jsonl
    2. conversation pluck → .data/$UUID/conversation.json
    3. index pluck → .data/$UUID/cdp.jsonl.d/index-pages.jsonl; filter to
       .uuid == $UUID → the sidebar's item, if any
    4. cross-check conversation doc vs sidebar item, null-tolerant
    5. choose meta: on disk, else sidebar (UserError if neither, or if
       they disagree)
    6. place_meta (writes meta.json, purges + places view dir-symlink)
    7. delegate to path_render

Captures are written directly into `.data/$UUID/` — no temp staging.
If a later step fails, the captures remain there for inspection.
"""
from pathlib import Path
from typing import cast

import typed_json
from typed_json import JsonObject
from chatfs.cli import extract_cache
from chatfs.layout import chat_dir_for
from chatfs.provider.claude import layout as claude_layout
from chatfs.provider.claude.pluck import pluck_conversation, pluck_index_pages
from chatfs.provider.claude.types import IndexItem, is_index_item, is_index_page
from chatfs.shell import sh as chatfs_sh
from chatfs.shell.capture import capture, pluck
from chatfs.shell.place import place_meta
from chatfs.url_browse import choose_meta, null_tolerant_mismatches
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
        page = typed_json.loads(line)
        assert is_index_page(page), page
        matches.extend(item for item in page["data"] if item["uuid"] == uuid)
    assert all(
        m == matches[0] for m in matches
    ), f"index endpoint returned divergent items for {uuid}: {matches}"
    return matches[0] if matches else None


def read_meta(data_dir: Path) -> IndexItem | None:
    """The meta.json already in `data_dir`, or None if there is none."""
    path = data_dir / "meta.json"
    if not path.exists():
        return None
    meta = typed_json.loads(path.read_text())
    assert is_index_item(meta), meta
    return meta


def _identity(item: IndexItem) -> JsonObject:
    return {
        "uuid": item["uuid"],
        "name": item["name"],
        "created_at": item["created_at"],
    }


@reports_user_errors
def main() -> None:
    import os
    import sys

    root, rest = extract_cache(sys.argv[1:], os.environ, claude_layout.PROVIDER)
    if root is None or len(rest) != 1:
        print(f"usage: {sys.argv[0]} --cache <dir> <claude-url>", file=sys.stderr)
        sys.exit(2)
    (url,) = rest

    uuid = claude_layout.uuid_from_url(url)

    chat_dir = chat_dir_for(uuid, root)
    data_dir = capture(url, chat_dir, pluck_conversation)
    conversation = data_dir / "conversation.json"

    item = find_index_item(data_dir, uuid)

    if item is not None:
        conv_doc = typed_json.loads(conversation.read_text())
        assert isinstance(conv_doc, dict), conv_doc
        # IndexItem's fields are all str, so this is a safe reinterpretation, not an
        # unverified cast — TypedDict's synthesized Mapping view widens values to
        # `object`, which null_tolerant_mismatches can't recurse into.
        mismatches = null_tolerant_mismatches(conv_doc, cast(JsonObject, dict(item)))
        assert not mismatches, (
            f"meta fields disagree across conversation and index endpoints "
            f"for {uuid}: {mismatches}"
        )

    meta = choose_meta(
        uuid, read_meta(data_dir), item, _identity, claude_layout.PROVIDER
    )
    _ = place_meta(
        meta["uuid"],
        meta["name"],
        claude_layout.created_at(meta["created_at"]),
        meta,
        root,
        updated=claude_layout.updated_at(meta),
    )

    _ = chatfs_sh.run(
        [
            sys.executable,
            "-m",
            "chatfs.provider.claude.conversation.path_render",
            str(chat_dir),
        ],
    )


if __name__ == "__main__":
    main()
