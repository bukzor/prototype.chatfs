#!/usr/bin/env python3
"""Refresh the aistudio index: capture it, then place every chat it names.

Usage:
    chatfs-provider-aistudio-index --cache <dir>

The bare-noun driver for `index` -- `index browse | index splat` over
one `--cache`, joined by an OS pipe rather than composed by the user's
shell. Its stdout is splat's: one placement record per chat placed.

Run the two stages by hand instead when you want to see or filter the
pages in between; browse's stdout is the raw index pages, which are
bulky.
"""
from chatfs.cli import cache_root, extract_cache
from chatfs.provider.aistudio.layout import PROVIDER
from chatfs.shell import sh as chatfs_sh


def main() -> None:
    import os
    import sys

    root, rest = extract_cache(sys.argv[1:], os.environ, PROVIDER)
    if root is None or rest:
        print(f"usage: {sys.argv[0]} --cache <dir>", file=sys.stderr)
        sys.exit(2)
    cache = cache_root(root, PROVIDER)

    chatfs_sh.pipe(
        [sys.executable, "-m", "chatfs.provider.aistudio.index.browse", "--cache", cache],
        [sys.executable, "-m", "chatfs.provider.aistudio.index.splat", "--cache", cache],
    )


if __name__ == "__main__":
    main()
