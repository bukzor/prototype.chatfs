#!/usr/bin/env python3
"""Move one conversation's products (chat dir + view symlinks) into a
date-labelled subdir of the cache root's `trash/`.

Usage:
    chatfs-provider-claude-conversation-url-trash --cache <dir> <claude-url>

Moves the chat dir itself plus any view symlinks that point into it. After
moving each symlink, prunes the view-tree path upward, removing any
parents left empty; stops at the first non-empty ancestor (same behavior
as `rmdir -p`, which has no direct stdlib equivalent).

`trash/` sits beside `.chat/`/`.data/` at the cache root -- the cache
need not live inside any repository, so there is no repo trash/ to use,
and keeping the move within one filesystem keeps it a rename.
"""
from datetime import datetime
from pathlib import Path

from chatfs.cli import extract_cache
from chatfs.provider.claude.layout import PROVIDER, uuid_from_url
from chatfs.shell import sh as chatfs_sh


def rmdir_p(dir: Path) -> None:
    """Remove dir and each empty parent, stopping at the first non-empty one."""
    while True:
        try:
            dir.rmdir()
        except OSError:
            return
        dir = dir.parent


def main() -> None:
    import os
    import shutil
    import sys

    root, rest = extract_cache(sys.argv[1:], os.environ, PROVIDER)
    if root is None or len(rest) != 1:
        print(f"usage: {sys.argv[0]} --cache <dir> <claude-url>", file=sys.stderr)
        sys.exit(2)
    (url,) = rest

    uuid = uuid_from_url(url)

    trash = root / "trash" / f"{datetime.now():%Y-%m-%dT%H:%M:%S,%f}000"
    trash.mkdir(parents=True)

    _ = shutil.move(root / ".chat" / uuid, trash)

    for link in root.rglob("*"):
        if "trash" in link.relative_to(root).parts:
            continue  # already-trashed content (incl. this run's) is not a view
        if link.is_symlink() and uuid in str(link.readlink()):
            parent = link.parent
            _ = shutil.move(link, trash)
            rmdir_p(parent)

    chatfs_sh.log(f"Moved to: {trash}")


if __name__ == "__main__":
    main()
