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
    1. browse $url → staging/cdp.jsonl
    2. conversation pluck → staging/conversation.json
    3. index pluck → filter to .uuid == $UUID → meta (fail loudly if absent)
    4. cross-check conversation doc vs index item, null-tolerant
    5. move captures into .chat/$UUID/.data/
    6. place_meta (writes meta.json, purges + places view dir-symlink)
    7. delegate to path_render
"""
import json
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import urlparse

from chatfs_claude_layout import chat_dir_for, data_dir_for, place_meta
from chatfs_claude_types import IndexItem

HERE = Path(__file__).parent
INDEX_PLUCK = HERE / "chatfs_claude_index_pluck.jq"
CONVERSATION_PLUCK = HERE / "chatfs_claude_conversation_pluck.jq"
PATH_RENDER = HERE / "chatfs_claude_conversation_path_render.py"
ROOT = HERE / "chatfs.demo" / "claude"


def uuid_from_url(url: str) -> str:
    parts = urlparse(url).path.strip("/").split("/")
    assert len(parts) == 2 and parts[0] == "chat", url
    return parts[1]


def null_tolerant_mismatches(a: Mapping, b: Mapping) -> list[str]:
    """Top-level key comparison; missing or None on either side is ok."""
    out: list[str] = []
    for k in set(a) | set(b):
        va, vb = a.get(k), b.get(k)
        if va is None or vb is None:
            continue
        if va != vb:
            out.append(f"{k}: {va!r} != {vb!r}")
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
        page = json.loads(line)
        for item in page.get("data", []):
            if item.get("uuid") == uuid:
                matches.append(item)
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

    with tempfile.TemporaryDirectory(prefix="chatfs-url-browse.") as tmp:
        staging = Path(tmp)
        staged_cdp = staging / "cdp.jsonl"
        staged_conversation = staging / "conversation.json"

        print(f"Capturing {url} → {staged_cdp} ...", file=sys.stderr)
        with staged_cdp.open("wb") as f:
            subprocess.run(["har-browse", url], stdout=f, check=True)

        print(f"Plucking conversation → {staged_conversation} ...", file=sys.stderr)
        with staged_cdp.open("rb") as src, staged_conversation.open("wb") as dst:
            subprocess.run([str(CONVERSATION_PLUCK)], stdin=src, stdout=dst, check=True)

        item = find_index_item(staged_cdp, uuid)

        conv_doc = json.loads(staged_conversation.read_text())
        mismatches = null_tolerant_mismatches(conv_doc, item)
        assert not mismatches, (
            f"meta fields disagree across conversation and index endpoints "
            f"for {uuid}: {mismatches}"
        )

        data_dir = data_dir_for(uuid, ROOT)
        data_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(staged_cdp), data_dir / "cdp.jsonl")
        shutil.move(str(staged_conversation), data_dir / "conversation.json")
        place_meta(item, ROOT)

    subprocess.run([str(PATH_RENDER), str(chat_dir_for(uuid, ROOT))], check=True)


if __name__ == "__main__":
    main()
