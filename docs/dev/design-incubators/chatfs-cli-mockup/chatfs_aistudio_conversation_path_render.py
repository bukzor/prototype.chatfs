#!/usr/bin/env python3
"""Render an AI Studio conversation from already-captured artifacts.

Usage:
    chatfs_aistudio_conversation_path_render.py <path-to-chat-dir-or-inside>

Prerequisites in the resolved chat dir:
    .data/meta.json           — placed by conversation url browse
    .data/conversation.json   — output of conversation pluck + massage

Steps:
    1. purge non-captured contents (allowlist {".data"})
    2. splat .data/conversation.json → .data/conversation.splat/
    3. move .data/conversation.splat/messages up to chat dir;
       rmdir .data/conversation.splat
    4. render → chat.md
"""
import shutil
import subprocess
import sys
from pathlib import Path

from chatfs_aistudio_layout import DATA_DIR_NAME, resolve_chat_dir


def purge_non_captured(chat_dir: Path) -> None:
    keep = {DATA_DIR_NAME}
    for child in chat_dir.iterdir():
        if child.name in keep:
            continue
        if child.is_symlink() or not child.is_dir():
            child.unlink()
        else:
            shutil.rmtree(child)


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path-to-chat-dir-or-inside>", file=sys.stderr)
        sys.exit(2)

    chat_dir = resolve_chat_dir(sys.argv[1])
    data_dir = chat_dir / DATA_DIR_NAME
    meta_path = data_dir / "meta.json"
    assert meta_path.exists(), (
        f"missing meta.json: run conversation url browse first ({meta_path})"
    )
    conversation = data_dir / "conversation.json"
    assert conversation.exists(), (
        f"missing conversation.json: run conversation url browse first ({conversation})"
    )

    purge_non_captured(chat_dir)

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
