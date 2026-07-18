#!/usr/bin/env python3
"""Render an AI Studio conversation from already-captured artifacts.

Usage:
    chatfs_aistudio_conversation_path_render.py <path-to-chat-dir-or-inside>

Prerequisites in the resolved chat dir's `.data/$id/` twin:
    meta.json           — placed by conversation url browse
    conversation.json   — output of conversation pluck + massage

Builds the entire derived surface (messages/, chat.md, the .data
inspection symlink) in a staged scratch sibling and atomically promotes
it over chat_dir in one swap -- readers see the old complete chat dir
or the new one, never partial or mixed. See chatfs_atomic.py's module
docstring for the mechanism; `staged` takes data_dir's write lock
itself (from chatfs_locks, reentrant), so no separate lock acquisition
is needed here.
"""
import sys
from pathlib import Path

import chatfs_sh
from chatfs_atomic import staged
from chatfs_aistudio_layout import data_dir_of, link_data_dir, resolve_chat_dir


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path-to-chat-dir-or-inside>", file=sys.stderr)
        sys.exit(2)

    chat_dir = resolve_chat_dir(sys.argv[1])
    uuid = chat_dir.name
    data_dir = data_dir_of(chat_dir)
    meta_path = data_dir / "meta.json"
    assert meta_path.exists(), (
        f"missing meta.json: run conversation url browse first ({meta_path})"
    )
    conversation = data_dir / "conversation.json"
    assert conversation.exists(), (
        f"missing conversation.json: run conversation url browse first ({conversation})"
    )

    here = Path(__file__).parent
    splat_script = here / "chatfs_aistudio_conversation_splat.py"
    render = here / "chatfs_aistudio_conversation_render.py"

    with staged(chat_dir, anchor=data_dir) as tmp:
        tmp.mkdir(parents=True)
        link_data_dir(tmp, uuid)

        print(f"Splatting {conversation} ...", file=sys.stderr)
        _ = chatfs_sh.run([str(splat_script), str(conversation), str(tmp)])

        out = tmp / "chat.md"
        print(f"Rendering {tmp} → chat.md ...", file=sys.stderr)
        with out.open("wb") as f:
            _ = chatfs_sh.run([str(render), str(tmp)], stdout=f)


if __name__ == "__main__":
    main()
