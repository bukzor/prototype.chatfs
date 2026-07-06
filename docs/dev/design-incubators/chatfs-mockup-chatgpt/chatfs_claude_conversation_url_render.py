#!/usr/bin/env python3
"""Render a claude conversation by URL, using already-captured artifacts.

Usage:
    chatfs_claude_conversation_url_render.py <claude-url>

Resolves the conversation UUID from the URL and delegates to
chatfs_claude_conversation_path_render.py against `.chat/$UUID/`.
"""
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

from chatfs_claude_layout import DATA_DIR_NAME, chat_dir_for

ROOT = Path(__file__).parent / "chatfs.demo" / "claude"


def uuid_from_url(url: str) -> str:
    parts = urlparse(url).path.strip("/").split("/")
    assert len(parts) == 2 and parts[0] == "chat", url
    return parts[1]


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <claude-url>", file=sys.stderr)
        sys.exit(2)

    chat_dir = chat_dir_for(uuid_from_url(sys.argv[1]), ROOT)
    assert (chat_dir / DATA_DIR_NAME / "meta.json").exists(), (
        f"chat not yet placed: {chat_dir} (run index browse first)"
    )

    path_render = Path(__file__).parent / "chatfs_claude_conversation_path_render.py"
    _ = subprocess.run([str(path_render), str(chat_dir)], check=True)


if __name__ == "__main__":
    main()
