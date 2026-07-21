#!/usr/bin/env python3
"""Capture chatgpt.com's conversation index.

Usage:
    python -m chatfs.provider.chatgpt.index.browse

stdout: one /backend-api/conversations page per line (jsonl).
"""
from chatfs.layout import DATA_DIR_NAME
from chatfs.paths import demo_root
from chatfs.provider.chatgpt.pluck import pluck_index_pages
from chatfs.shell.capture import browse, dump_jsonl

ROOT = demo_root("chatgpt")
CDP = ROOT / DATA_DIR_NAME / "index.cdp.jsonl"  # debug intermediate

URL = "https://chatgpt.com"


def main() -> None:
    import sys

    CDP.parent.mkdir(parents=True, exist_ok=True)
    browse(URL, CDP)
    with CDP.open() as f:
        dump_jsonl(pluck_index_pages(f), sys.stdout)


if __name__ == "__main__":
    main()
