#!/usr/bin/env python3
"""Capture aistudio.google.com's prompt index.

Usage:
    chatfs_aistudio_index_browse.py

stdout: one index entry per line (jsonl) — pluck flattens every
ListPrompts response it sees, so this catches as many pages as
har-browse's session actually triggers. This account's 42 prompts fit
one page, so a scroll-triggered second page is unverified here — same
har-browse "wait until has_more=false" gap tracked for claude (todo.md).
"""
import sys
from pathlib import Path

from chatfs_aistudio_layout import pluck_index_pages
from chatfs_layout import DATA_DIR_NAME, browse, dump_jsonl

ROOT = Path(__file__).parent / "chatfs.demo" / "aistudio"
CDP = ROOT / DATA_DIR_NAME / "index.cdp.jsonl"  # debug intermediate

URL = "https://aistudio.google.com/library"


def main() -> None:
    CDP.parent.mkdir(parents=True, exist_ok=True)
    browse(URL, CDP)
    with CDP.open() as f:
        dump_jsonl(pluck_index_pages(f), sys.stdout)


if __name__ == "__main__":
    main()
