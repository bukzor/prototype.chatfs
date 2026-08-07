#!/usr/bin/env python3
"""Render an AI Studio conversation by URL, using already-captured artifacts.

Usage:
    python -m chatfs.provider.aistudio.conversation.url_render <aistudio-url>

Resolves the conversation id from the URL and delegates to path_render
against `.chat/$id/`, as a subprocess (see path_render's own module
docstring for why).
"""
from chatfs.layout import chat_dir_for, data_dir_for
from chatfs.paths import INCUBATOR_ROOT, demo_root
from chatfs.provider.aistudio import layout as aistudio_layout
from chatfs.shell import sh as chatfs_sh

ROOT = demo_root("aistudio")


def main() -> None:
    import sys

    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <aistudio-url>", file=sys.stderr)
        sys.exit(2)

    id_ = aistudio_layout.uuid_from_url(sys.argv[1])
    chat_dir = chat_dir_for(id_, ROOT)
    assert (data_dir_for(id_, ROOT) / "meta.json").exists(), (
        f"chat not yet placed: {chat_dir} (run conversation url browse first)"
    )

    _ = chatfs_sh.run(
        [
            sys.executable,
            "-m",
            "chatfs.provider.aistudio.conversation.path_render",
            str(chat_dir),
        ],
        cwd=INCUBATOR_ROOT,
    )


if __name__ == "__main__":
    main()
