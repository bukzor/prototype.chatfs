#!/usr/bin/env python3
"""Render a chatgpt conversation by URL, using already-captured artifacts.

Usage:
    chatfs-chatgpt-conversation-url-render --cache <dir> <chatgpt-url>

Resolves the conversation UUID from the URL and delegates to path_render
against `.chat/$UUID/`, as a subprocess (see path_render's own module
docstring for why).
"""
from chatfs.cli import extract_cache
from chatfs.layout import chat_dir_for, data_dir_for
from chatfs.provider.chatgpt import layout as chatgpt_layout
from chatfs.shell import sh as chatfs_sh


def main() -> None:
    import os
    import sys

    root, rest = extract_cache(sys.argv[1:], os.environ, chatgpt_layout.PROVIDER)
    if root is None or len(rest) != 1:
        print(f"usage: {sys.argv[0]} --cache <dir> <chatgpt-url>", file=sys.stderr)
        sys.exit(2)
    (url,) = rest

    uuid = chatgpt_layout.uuid_from_url(url)
    chat_dir = chat_dir_for(uuid, root)
    assert (data_dir_for(uuid, root) / "meta.json").exists(), (
        f"chat not yet placed: {chat_dir} (run index browse first)"
    )

    _ = chatfs_sh.run(
        [
            sys.executable,
            "-m",
            "chatfs.provider.chatgpt.conversation.path_render",
            str(chat_dir),
        ],
    )


if __name__ == "__main__":
    main()
