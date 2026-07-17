#!/usr/bin/env python3
"""Render an AI Studio conversation from already-captured artifacts.

Usage:
    chatfs_aistudio_conversation_path_render.py <path-to-chat-dir-or-inside>

Prerequisites in the resolved chat dir's `.data/$id/` twin:
    meta.json           — placed by conversation url browse
    conversation.json   — output of conversation pluck + massage

Steps:
    1. reset the chat dir (100% derived; nothing survives a rebuild)
    2. splat .data/$id/conversation.json → .data/$id/conversation.splat/
    3. move .data/$id/conversation.splat/messages up to chat dir;
       rmdir .data/$id/conversation.splat
    4. relink chat dir/.data -> .data/$id (inspection symlink)
    5. render → chat.md
"""
import shutil
import subprocess
import sys
from pathlib import Path

from chatfs_aistudio_layout import data_dir_of, link_data_dir, resolve_chat_dir


def purge_non_captured(chat_dir: Path) -> None:
    """Reset chat_dir to empty. Nothing under it is captured anymore --
    captured exhaust lives in the parallel `.data/$id/` tree -- so
    there is no allowlist to preserve."""
    if chat_dir.exists():
        shutil.rmtree(chat_dir)
    chat_dir.mkdir(parents=True)


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path-to-chat-dir-or-inside>", file=sys.stderr)
        sys.exit(2)

    chat_dir = resolve_chat_dir(sys.argv[1])
    data_dir = data_dir_of(chat_dir)
    meta_path = data_dir / "meta.json"
    assert meta_path.exists(), (
        f"missing meta.json: run conversation url browse first ({meta_path})"
    )
    conversation = data_dir / "conversation.json"
    assert conversation.exists(), (
        f"missing conversation.json: run conversation url browse first ({conversation})"
    )

    purge_non_captured(chat_dir)
    link_data_dir(chat_dir, chat_dir.name)

    here = Path(__file__).parent
    splat_script = here / "chatfs_aistudio_conversation_splat.py"
    print(f"Splatting {conversation} ...", file=sys.stderr)
    _ = subprocess.run([str(splat_script), str(conversation)], check=True)
    splat = data_dir / "conversation.splat"
    for entry in splat.iterdir():
        _ = shutil.move(str(entry), str(chat_dir / entry.name))
    splat.rmdir()

    render = here / "chatfs_aistudio_conversation_render.py"
    out = chat_dir / "chat.md"
    print(f"Rendering {chat_dir} → chat.md ...", file=sys.stderr)
    with out.open("wb") as f:
        _ = subprocess.run([str(render), str(chat_dir)], stdout=f, check=True)


if __name__ == "__main__":
    main()
