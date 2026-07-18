#!/usr/bin/env python3
"""Move the products of `chatfs_claude_conversation_url_browse.py <url>`
into a date-labelled subdir of repo-root `trash/`.

Usage:
    chatfs_claude_conversation_url_trash.py <claude-url>

Moves the chat dir itself plus any view symlinks that point into it. After
moving each symlink, prunes the view-tree path upward, removing any
parents left empty; stops at the first non-empty ancestor (same behavior
as `rmdir -p`, which has no direct stdlib equivalent).
"""
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from chatfs_claude_conversation_url_browse import uuid_from_url

HERE = Path(__file__).parent
ROOT = HERE / "chatfs.demo" / "claude"


def rmdir_p(dir: Path) -> None:
    """Remove dir and each empty parent, stopping at the first non-empty one."""
    while True:
        try:
            dir.rmdir()
        except OSError:
            return
        dir = dir.parent


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <claude-url>", file=sys.stderr)
        sys.exit(2)

    uuid = uuid_from_url(sys.argv[1])

    repo_root = Path(
        subprocess.run(
            ["git", "-C", str(HERE), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    trash = repo_root / "trash" / f"{datetime.now():%Y-%m-%dT%H:%M:%S,%f}000"
    trash.mkdir(parents=True)

    _ = shutil.move(ROOT / ".chat" / uuid, trash)

    for link in ROOT.rglob("*"):
        if link.is_symlink() and uuid in str(link.readlink()):
            parent = link.parent
            _ = shutil.move(link, trash)
            rmdir_p(parent)

    print(f"Moved to: {trash}", file=sys.stderr)


if __name__ == "__main__":
    main()
