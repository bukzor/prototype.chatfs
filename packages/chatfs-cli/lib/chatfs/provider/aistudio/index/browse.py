#!/usr/bin/env python3
"""Capture aistudio.google.com's prompt index.

Usage:
    chatfs-provider-aistudio-index-browse --cache <dir>

stdout: one index entry per line (jsonl) — pluck flattens every
ListPrompts response it sees, so this catches as many pages as
har-browse's session actually triggers. This account's 42 prompts fit
one page, so a scroll-triggered second page is unverified here — same
har-browse "wait until has_more=false" gap tracked for claude (todo.md).
"""
from chatfs.cli import extract_cache
from chatfs.layout import DATA_DIR_NAME
from chatfs.provider.aistudio.layout import PROVIDER
from chatfs.provider.aistudio.pluck import pluck_index_pages
from chatfs.shell.capture import browse, dump_jsonl

URL = "https://aistudio.google.com/library"


def main() -> None:
    import os
    import sys

    root, rest = extract_cache(sys.argv[1:], os.environ, PROVIDER)
    if root is None or rest:
        print(f"usage: {sys.argv[0]} --cache <dir>", file=sys.stderr)
        sys.exit(2)

    cdp = root / DATA_DIR_NAME / "index.cdp.jsonl"  # debug intermediate
    cdp.parent.mkdir(parents=True, exist_ok=True)
    browse(URL, cdp)
    with cdp.open() as f:
        dump_jsonl(pluck_index_pages(f), sys.stdout)


if __name__ == "__main__":
    main()
