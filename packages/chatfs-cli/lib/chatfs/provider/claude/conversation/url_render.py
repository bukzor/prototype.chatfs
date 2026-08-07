#!/usr/bin/env python3
"""Render a claude conversation by URL, using already-captured artifacts.

Usage:
    chatfs-claude-conversation-url-render --cache <dir> <claude-url>

Resolves the conversation UUID from the URL and delegates to path_render
against `.chat/$UUID/`, as a subprocess (see path_render's own module
docstring for why).
"""
from pathlib import Path

from chatfs.layout import chat_dir_for, data_dir_for
from chatfs.provider.claude import layout as claude_layout
from chatfs.shell import sh as chatfs_sh


def main() -> None:
    import sys

    match sys.argv[1:]:
        case ["--cache", cache, url]:
            root = Path(cache)
        case _:
            print(f"usage: {sys.argv[0]} --cache <dir> <claude-url>", file=sys.stderr)
            sys.exit(2)

    uuid = claude_layout.uuid_from_url(url)
    chat_dir = chat_dir_for(uuid, root)
    assert (data_dir_for(uuid, root) / "meta.json").exists(), (
        f"chat not yet placed: {chat_dir} (run index browse first)"
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
