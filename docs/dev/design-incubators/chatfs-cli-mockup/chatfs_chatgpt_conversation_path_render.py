#!/usr/bin/env python3
"""Render a conversation from already-captured artifacts.

Usage:
    chatfs_chatgpt_conversation_path_render.py <path-to-chat-dir-or-inside>

Prerequisites in the resolved chat dir's `.data/$UUID/` twin:
    meta.json           — placed by index splat or url browse
    conversation.json   — output of conversation pluck

Builds the entire derived surface (messages/, conversations/, chat.md,
the .data inspection symlink) in a staged scratch sibling and
atomically promotes it over chat_dir in one swap -- readers see the
old complete chat dir or the new one, never partial or mixed. See
chatfs_atomic.py's module docstring for the mechanism; write_locked
comes from chatfs_locks (not chatfs_atomic) so this script's own lock
acquisition is safe to re-enter from an ancestor process that already
holds it.
"""
import subprocess
import sys
from pathlib import Path

from chatfs_atomic import staged
from chatfs_chatgpt_layout import data_dir_of, link_data_dir, resolve_chat_dir
from chatfs_locks import write_locked


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path-to-chat-dir-or-inside>", file=sys.stderr)
        sys.exit(2)

    chat_dir = resolve_chat_dir(sys.argv[1])
    uuid = chat_dir.name
    data_dir = data_dir_of(chat_dir)
    meta_path = data_dir / "meta.json"
    assert meta_path.exists(), f"missing meta.json: run index browse first ({meta_path})"
    conversation = data_dir / "conversation.json"
    assert conversation.exists(), (
        f"missing conversation.json: run conversation browse first ({conversation})"
    )

    render = Path(__file__).parent / "chatfs_chatgpt_conversation_render.py"

    with write_locked(data_dir):
        with staged(chat_dir) as tmp:
            tmp.mkdir(parents=True)
            link_data_dir(tmp, uuid)

            print(f"Splatting {conversation} ...", file=sys.stderr)
            _ = subprocess.run(["chatgpt-splat", str(conversation), str(tmp)], check=True)

            out = tmp / "chat.md"
            print(f"Rendering {tmp} → chat.md ...", file=sys.stderr)
            with out.open("wb") as f:
                _ = subprocess.run([str(render), str(tmp)], stdout=f, check=True)


if __name__ == "__main__":
    main()
