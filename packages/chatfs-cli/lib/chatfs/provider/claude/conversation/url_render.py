#!/usr/bin/env python3
"""Render a claude conversation by URL, using already-captured artifacts.

Usage:
    python -m chatfs.provider.claude.conversation.url_render <claude-url>

Resolves the conversation UUID from the URL and delegates to path_render
against `.chat/$UUID/`, as a subprocess (see path_render's own module
docstring for why).
"""
from chatfs.layout import chat_dir_for, data_dir_for
from chatfs.paths import INCUBATOR_ROOT, demo_root
from chatfs.provider.claude import layout as claude_layout
from chatfs.shell import sh as chatfs_sh

ROOT = demo_root("claude")


def main() -> None:
    import sys

    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <claude-url>", file=sys.stderr)
        sys.exit(2)

    uuid = claude_layout.uuid_from_url(sys.argv[1])
    chat_dir = chat_dir_for(uuid, ROOT)
    assert (data_dir_for(uuid, ROOT) / "meta.json").exists(), (
        f"chat not yet placed: {chat_dir} (run index browse first)"
    )

    _ = chatfs_sh.run(
        [
            sys.executable,
            "-m",
            "chatfs.provider.claude.conversation.path_render",
            str(chat_dir),
        ],
        cwd=INCUBATOR_ROOT,
    )


if __name__ == "__main__":
    main()
