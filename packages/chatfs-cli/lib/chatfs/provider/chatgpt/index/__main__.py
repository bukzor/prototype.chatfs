#!/usr/bin/env python3
"""Refresh the chatgpt index: capture it, then place every chat it names.

Usage:
    chatfs-chatgpt-index --cache <dir>

The bare-noun driver for `index` -- `index browse | index splat` over
one `--cache`, joined by an OS pipe rather than composed by the user's
shell. Run the two stages by hand instead when you want to see or
filter the pages in between; browse's stdout is the raw index pages,
which are bulky.
"""
from chatfs.cli import extract_cache
from chatfs.shell import sh as chatfs_sh


def main() -> None:
    import os
    import sys

    root, rest = extract_cache(sys.argv[1:], os.environ)
    if root is None or rest:
        print(f"usage: {sys.argv[0]} --cache <dir>", file=sys.stderr)
        sys.exit(2)

    chatfs_sh.pipe(
        [sys.executable, "-m", "chatfs.provider.chatgpt.index.browse", "--cache", root],
        [sys.executable, "-m", "chatfs.provider.chatgpt.index.splat", "--cache", root],
    )


if __name__ == "__main__":
    main()
