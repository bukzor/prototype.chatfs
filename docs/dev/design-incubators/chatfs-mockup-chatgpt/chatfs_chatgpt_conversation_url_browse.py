#!/usr/bin/env python3
"""Capture a chatgpt.com conversation by URL.

Usage:
    chatfs_chatgpt_conversation_url_browse.py <chatgpt-url>

One browse call captures both the conversation document and the sidebar
index page that mentions it (see browse-incidental-capture.md). We use
the latter to derive `meta.json` byte-for-byte from the index endpoint,
avoiding partial synthesis.

Steps:
    1. browse $url → staging/cdp.jsonl
    2. conversation pluck → staging/conversation.json
    3. index pluck → filter to .id == $UUID → meta (fail loudly if absent)
    4. ensure .chat/$UUID/.data/ exists; move captures into it
    5. place_meta (writes meta.json, purges + places view dir-symlink)
    6. delegate to path_render (splat + render)
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from chatfs_chatgpt_layout import chat_dir_for, data_dir_for, place_meta
from chatfs_chatgpt_types import IndexItem

HERE = Path(__file__).parent
INDEX_PLUCK = HERE / "chatfs_chatgpt_index_pluck.jq"
CONVERSATION_PLUCK = HERE / "chatfs_chatgpt_conversation_pluck.jq"
PATH_RENDER = HERE / "chatfs_chatgpt_conversation_path_render.py"
ROOT = HERE / "chatfs.demo" / "chatgpt"


def uuid_from_url(url: str) -> str:
    parts = urlparse(url).path.strip("/").split("/")
    assert len(parts) == 2 and parts[0] == "c", url
    return parts[1]


def find_index_item(cdp: Path, uuid: str) -> IndexItem:
    """Run index pluck; return the single item matching uuid.

    Fails loudly if no sidebar page included this conversation — the
    user's recovery is to run `index browse` then `conversation path
    browse` against the resulting chat dir.
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
        for item in page.get("items", []):
            if item.get("id") == uuid:
                matches.append(item)
    assert matches, (
        f"no sidebar index page included {uuid}; "
        f"run `chatfs_chatgpt_index_browse.sh` and use `conversation_path_browse.py`"
    )
    assert all(m == matches[0] for m in matches), (
        f"index endpoint returned divergent items for {uuid}: {matches}"
    )
    return matches[0]


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <chatgpt-url>", file=sys.stderr)
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
        data_dir = data_dir_for(uuid, ROOT)
        data_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(staged_cdp), data_dir / "cdp.jsonl")
        shutil.move(str(staged_conversation), data_dir / "conversation.json")
        place_meta(item, ROOT)

    subprocess.run([str(PATH_RENDER), str(chat_dir_for(uuid, ROOT))], check=True)


if __name__ == "__main__":
    main()
