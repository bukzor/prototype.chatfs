#!/usr/bin/env python3
"""Render a conversation from already-plucked artifacts.

Usage:
    chatfs_chatgpt_conversation_path_render.py <path-inside-page-dir>

Prerequisites (errors otherwise):
    $page/meta.json       — placed by index splat
    $page/$UUID.json      — output of conversation pluck

Steps:
    1. splat $UUID.json → $UUID.splat/
    2. render → $TITLE.md
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

from chatfs_chatgpt_layout import safe_filename


def page_dir_for(arg: str) -> Path:
    p = Path(arg)
    if p.exists(follow_symlinks=False) and not p.is_dir():
        p = p.parent
    return p


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path-inside-page-dir>", file=sys.stderr)
        sys.exit(2)

    page = page_dir_for(sys.argv[1])
    meta_path = page / "meta.json"
    assert meta_path.exists(), f"missing meta.json: run index browse first ({meta_path})"

    meta = json.loads(meta_path.read_text())
    conversation = page / f"{meta['id']}.json"
    assert conversation.exists(), (
        f"missing pluck output: run conversation browse first ({conversation})"
    )

    splat = page / f"{meta['id']}.splat"
    if splat.exists():
        shutil.rmtree(splat)
    print(f"Splatting {conversation} ...", file=sys.stderr)
    subprocess.run(["chatgpt-splat", str(conversation)], check=True)

    render = Path(__file__).parent / "chatfs_chatgpt_conversation_render.py"
    out = page / f"{safe_filename(meta['title'])}.md"
    out.unlink(missing_ok=True)
    print(f"Rendering {page} → {out.name} ...", file=sys.stderr)
    with out.open("wb") as f:
        subprocess.run([str(render), str(page)], stdout=f, check=True)


if __name__ == "__main__":
    main()
