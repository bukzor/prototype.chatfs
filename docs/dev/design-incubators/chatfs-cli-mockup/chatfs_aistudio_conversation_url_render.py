#!/usr/bin/env python3
"""Render an AI Studio conversation by URL, using already-captured artifacts.

Usage:
    chatfs_aistudio_conversation_url_render.py <aistudio-url>

Resolves the conversation id from the URL and delegates to
chatfs_aistudio_conversation_path_render.py against `.chat/$id/`.
"""
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

from chatfs_aistudio_layout import DATA_DIR_NAME, chat_dir_for

ROOT = Path(__file__).parent / "chatfs.demo" / "aistudio"


def id_from_url(url: str) -> str:
    parts = urlparse(url).path.strip("/").split("/")
    assert len(parts) == 2 and parts[0] == "prompts", url
    return parts[1]


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <aistudio-url>", file=sys.stderr)
        sys.exit(2)

    chat_dir = chat_dir_for(id_from_url(sys.argv[1]), ROOT)
    assert (chat_dir / DATA_DIR_NAME / "meta.json").exists(), (
        f"chat not yet placed: {chat_dir} (run conversation url browse first)"
    )

    path_render = Path(__file__).parent / "chatfs_aistudio_conversation_path_render.py"
    _ = subprocess.run([str(path_render), str(chat_dir)], check=True)


if __name__ == "__main__":
    main()
