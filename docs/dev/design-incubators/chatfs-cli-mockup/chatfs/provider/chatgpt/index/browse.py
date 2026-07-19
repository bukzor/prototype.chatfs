#!/usr/bin/env python3
"""Capture chatgpt.com's conversation index.

Usage:
    chatfs_chatgpt_index_browse.py

stdout: one /backend-api/conversations page per line (jsonl).
"""
import sys
from pathlib import Path

from chatfs_chatgpt_layout import pluck_index_pages
from chatfs_layout import DATA_DIR_NAME, browse, dump_jsonl

ROOT = Path(__file__).parent / "chatfs.demo" / "chatgpt"
CDP = ROOT / DATA_DIR_NAME / "index.cdp.jsonl"  # debug intermediate

URL = "https://chatgpt.com"


def main() -> None:
    CDP.parent.mkdir(parents=True, exist_ok=True)
    browse(URL, CDP)
    with CDP.open() as f:
        dump_jsonl(pluck_index_pages(f), sys.stdout)


if __name__ == "__main__":
    main()
