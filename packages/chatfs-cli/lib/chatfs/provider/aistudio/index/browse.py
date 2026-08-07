#!/usr/bin/env python3
"""Capture aistudio.google.com's prompt index.

Usage:
    python -m chatfs.provider.aistudio.index.browse

stdout: one index entry per line (jsonl) — pluck flattens every
ListPrompts response it sees, so this catches as many pages as
har-browse's session actually triggers. This account's 42 prompts fit
one page, so a scroll-triggered second page is unverified here — same
har-browse "wait until has_more=false" gap tracked for claude (todo.md).
"""
from chatfs.layout import DATA_DIR_NAME
from chatfs.paths import demo_root
from chatfs.provider.aistudio.pluck import pluck_index_pages
from chatfs.shell.capture import browse, dump_jsonl

ROOT = demo_root("aistudio")
CDP = ROOT / DATA_DIR_NAME / "index.cdp.jsonl"  # debug intermediate

URL = "https://aistudio.google.com/library"


def main() -> None:
    import sys

    CDP.parent.mkdir(parents=True, exist_ok=True)
    browse(URL, CDP)
    with CDP.open() as f:
        dump_jsonl(pluck_index_pages(f), sys.stdout)


if __name__ == "__main__":
    main()
