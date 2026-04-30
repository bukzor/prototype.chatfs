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
    2. conversation pluck → staging/$UUID.json
    3. index pluck → filter to .id == $UUID → meta (fail loudly if absent)
    4. derive ts-dir from meta.create_time; rm -rf and rebuild
    5. place meta.json (via place_meta), move cdp.jsonl + $UUID.json
    6. delegate to path_render (splat + render)
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from chatfs_chatgpt_layout import place_meta, time_dir_for
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
    browse` against the resulting ts-dir.
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
    return matches[0]


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <chatgpt-url>", file=sys.stderr)
        sys.exit(2)

    url = sys.argv[1]
    uuid = uuid_from_url(url)

    with tempfile.TemporaryDirectory(prefix="chatfs-url-browse.") as tmp:
        staging = Path(tmp)
        cdp = staging / "cdp.jsonl"
        conversation = staging / f"{uuid}.json"

        print(f"Capturing {url} → {cdp} ...", file=sys.stderr)
        with cdp.open("wb") as f:
            subprocess.run(["har-browse", url], stdout=f, check=True)

        print(f"Plucking conversation → {conversation} ...", file=sys.stderr)
        with cdp.open("rb") as src, conversation.open("wb") as dst:
            subprocess.run([str(CONVERSATION_PLUCK)], stdin=src, stdout=dst, check=True)

        item = find_index_item(cdp, uuid)
        page = ROOT / time_dir_for(item["create_time"])
        if page.exists():
            shutil.rmtree(page)
        ROOT.mkdir(parents=True, exist_ok=True)
        place_meta(item, ROOT)

        shutil.move(str(cdp), page / "cdp.jsonl")
        shutil.move(str(conversation), page / f"{uuid}.json")

    subprocess.run([str(PATH_RENDER), str(page)], check=True)


if __name__ == "__main__":
    main()
