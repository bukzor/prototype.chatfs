#!/usr/bin/env python3
"""Render an AI Studio conversation by URL, using already-captured artifacts.

Usage:
    chatfs_aistudio_conversation_url_render.py <aistudio-url>

Resolves the conversation id from the URL and delegates to
chatfs_aistudio_conversation_path_render.py against `.chat/$id/`.
"""
import sys
from pathlib import Path
from urllib.parse import urlparse

import chatfs_sh
from chatfs_aistudio_layout import chat_dir_for, data_dir_for

ROOT = Path(__file__).parent / "chatfs.demo" / "aistudio"


def id_from_url(url: str) -> str:
    parts = urlparse(url).path.strip("/").split("/")
    assert len(parts) == 2 and parts[0] == "prompts", url
    return parts[1]


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <aistudio-url>", file=sys.stderr)
        sys.exit(2)

    id_ = id_from_url(sys.argv[1])
    chat_dir = chat_dir_for(id_, ROOT)
    assert (data_dir_for(id_, ROOT) / "meta.json").exists(), (
        f"chat not yet placed: {chat_dir} (run conversation url browse first)"
    )

    path_render = Path(__file__).parent / "chatfs_aistudio_conversation_path_render.py"
    _ = chatfs_sh.run([str(path_render), str(chat_dir)])


if __name__ == "__main__":
    main()
