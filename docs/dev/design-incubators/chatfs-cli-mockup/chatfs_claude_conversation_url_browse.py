#!/usr/bin/env python3
"""Capture a claude.ai conversation by URL.

Usage:
    chatfs_claude_conversation_url_browse.py <claude-url>

Assumes (per browse-incidental-capture.md) that visiting `/chat/$UUID`
also fires `/chat_conversations_v2` for the sidebar, so one browse trip
captures both the conversation document and an index page that mentions
this UUID.

If that assumption is ever violated, `find_index_item` fails loudly and
the recovery path is two-step: `chatfs_claude_index_browse.sh` →
`chatfs_claude_index_splat.py` → `chatfs_claude_conversation_path_browse.py`.

A second cross-check asserts that the meta-shaped fields agree across
the two endpoints (null-tolerant) — catches schema drift if either side
ever changes shape.

Steps:
    1. browse $url → .chat/$UUID/.data/cdp.jsonl
    2. conversation pluck → .chat/$UUID/.data/conversation.json
    3. index pluck → filter to .uuid == $UUID → meta (fail loudly if absent)
    4. cross-check conversation doc vs index item, null-tolerant
    5. place_meta (writes meta.json, purges + places view dir-symlink)
    6. delegate to path_render

Captures are written directly into `.chat/$UUID/.data/` — no temp
staging. If a later step fails, the captures remain there for
inspection. Recovery from the long-tail "sidebar didn't include this
uuid" case is to run `chatfs_claude_index_browse.sh |
chatfs_claude_index_splat.py` (deposits meta.json into the same
`.data/`) and then `chatfs_claude_conversation_path_render.py` on the
chat dir (reuses the already-captured cdp.jsonl + conversation.json).
"""
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import cast
from urllib.parse import urlparse

import chatfs_json
from chatfs_claude_layout import capture, chat_dir_for, place_meta
from chatfs_claude_types import IndexItem, is_index_page
from chatfs_json import JsonObject, JsonValue

HERE = Path(__file__).parent
INDEX_PLUCK = HERE / "chatfs_claude_index_pluck.jq"
PATH_RENDER = HERE / "chatfs_claude_conversation_path_render.py"
ROOT = HERE / "chatfs.demo" / "claude"


def uuid_from_url(url: str) -> str:
    parts = urlparse(url).path.strip("/").split("/")
    assert len(parts) == 2 and parts[0] == "chat", url
    return parts[1]


def null_tolerant_mismatches(
    a: Mapping[str, JsonValue], b: Mapping[str, JsonValue], prefix: str = ""
) -> list[str]:
    """Recursive key comparison; missing or None on either side is ok.

    Recurses into nested mappings so that one side carrying extra
    None-valued keys (common when one endpoint returns a superset
    schema with unset fields) does not register as a mismatch.
    """
    out: list[str] = []
    for k in set(a) | set(b):
        va, vb = a.get(k), b.get(k)
        if va is None or vb is None:
            continue
        path = f"{prefix}{k}"
        if isinstance(va, Mapping) and isinstance(vb, Mapping):
            out.extend(null_tolerant_mismatches(va, vb, prefix=f"{path}."))
            continue
        if va != vb:
            out.append(f"{path}: {va!r} != {vb!r}")
    return out


def find_index_item(cdp: Path, uuid: str) -> IndexItem:
    """Pluck index pages from CDP; return the item matching uuid.

    Fails loudly if no incidentally-captured index page mentioned this
    uuid — recovery is the two-step (index_browse → index_splat →
    path_browse).
    """
    with cdp.open("rb") as src:
        result = subprocess.run(
            [str(INDEX_PLUCK)], stdin=src, capture_output=True, check=True
        )
    matches: list[IndexItem] = []
    for line in result.stdout.decode().splitlines():
        if not line.strip():
            continue
        page = chatfs_json.loads(line)
        assert is_index_page(page), page
        matches.extend(item for item in page["data"] if item["uuid"] == uuid)
    assert matches, (
        f"no sidebar index page included {uuid}; "
        f"run `chatfs_claude_index_browse.sh | chatfs_claude_index_splat.py`, "
        f"then use `chatfs_claude_conversation_path_browse.py`"
    )
    assert all(m == matches[0] for m in matches), (
        f"index endpoint returned divergent items for {uuid}: {matches}"
    )
    return matches[0]


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <claude-url>", file=sys.stderr)
        sys.exit(2)

    url = sys.argv[1]
    uuid = uuid_from_url(url)

    chat_dir = chat_dir_for(uuid, ROOT)
    data_dir = capture(url, chat_dir)
    cdp = data_dir / "cdp.jsonl"
    conversation = data_dir / "conversation.json"

    item = find_index_item(cdp, uuid)

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

    _ = place_meta(item, ROOT)

    _ = subprocess.run([str(PATH_RENDER), str(chat_dir)], check=True)


if __name__ == "__main__":
    main()
