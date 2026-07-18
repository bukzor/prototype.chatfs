#!/usr/bin/env python3
"""Render a claude conversation by URL, using already-captured artifacts.

Usage:
    chatfs_claude_conversation_url_render.py <claude-url>

Resolves the conversation UUID from the URL and delegates to
chatfs_claude_conversation_path_render.py against `.chat/$UUID/`.
"""
import sys
from pathlib import Path
from urllib.parse import urlparse

import chatfs_sh
from chatfs_claude_layout import chat_dir_for, data_dir_for

ROOT = Path(__file__).parent / "chatfs.demo" / "claude"


def uuid_from_url(url: str) -> str:
    parts = urlparse(url).path.strip("/").split("/")
    assert len(parts) == 2 and parts[0] == "chat", url
    return parts[1]


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <claude-url>", file=sys.stderr)
        sys.exit(2)

    uuid = uuid_from_url(sys.argv[1])
    chat_dir = chat_dir_for(uuid, ROOT)
    assert (data_dir_for(uuid, ROOT) / "meta.json").exists(), (
        f"chat not yet placed: {chat_dir} (run index browse first)"
    )

    path_render = Path(__file__).parent / "chatfs_claude_conversation_path_render.py"
    _ = chatfs_sh.run([str(path_render), str(chat_dir)])


if __name__ == "__main__":
    main()
