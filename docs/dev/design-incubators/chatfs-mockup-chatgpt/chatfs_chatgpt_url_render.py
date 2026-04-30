#!/usr/bin/env python3
"""Render a conversation by URL, using already-captured artifacts.

Usage:
    chatfs_chatgpt_url_render.py <chatgpt-url>

Resolves the conversation UUID from the URL, locates the corresponding
page directory under chatfs.demo/chatgpt/ (placed by index browse), and
delegates to chatfs_chatgpt_path_render.py.
"""
import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parent / "chatfs.demo" / "chatgpt"


def uuid_from_url(url: str) -> str:
    parts = urlparse(url).path.strip("/").split("/")
    assert len(parts) == 2 and parts[0] == "c", url
    return parts[1]


def page_for_uuid(uuid: str, root: Path) -> Path:
    matches = [
        meta.parent
        for meta in root.rglob("meta.json")
        if json.loads(meta.read_text()).get("id") == uuid
    ]
    assert len(matches) == 1, (uuid, matches)
    return matches[0]


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <chatgpt-url>", file=sys.stderr)
        sys.exit(2)

    uuid = uuid_from_url(sys.argv[1])
    page = page_for_uuid(uuid, ROOT)
    print(f"Resolved {uuid} → {page}", file=sys.stderr)

    path_render = Path(__file__).parent / "chatfs_chatgpt_path_render.py"
    subprocess.run([str(path_render), str(page)], check=True)


if __name__ == "__main__":
    main()
