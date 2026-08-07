#!/usr/bin/env python3
"""Render an AI Studio conversation by URL, using already-captured artifacts.

Usage:
    chatfs-aistudio-conversation-url-render --cache <dir> <aistudio-url>

Resolves the conversation id from the URL and delegates to path_render
against `.chat/$id/`, as a subprocess (see path_render's own module
docstring for why).
"""
from pathlib import Path

from chatfs.layout import chat_dir_for, data_dir_for
from chatfs.provider.aistudio import layout as aistudio_layout
from chatfs.shell import sh as chatfs_sh


def main() -> None:
    import sys

    match sys.argv[1:]:
        case ["--cache", cache, url]:
            root = Path(cache)
        case _:
            print(f"usage: {sys.argv[0]} --cache <dir> <aistudio-url>", file=sys.stderr)
            sys.exit(2)

    id_ = aistudio_layout.uuid_from_url(url)
    chat_dir = chat_dir_for(id_, root)
    assert (data_dir_for(id_, root) / "meta.json").exists(), (
        f"chat not yet placed: {chat_dir} (run conversation url browse first)"
    )

    _ = chatfs_sh.run(
        [
            sys.executable,
            "-m",
            "chatfs.provider.aistudio.conversation.path_render",
            str(chat_dir),
        ],
    )


if __name__ == "__main__":
    main()
