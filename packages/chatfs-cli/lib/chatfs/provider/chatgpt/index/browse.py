#!/usr/bin/env python3
"""Capture chatgpt.com's conversation index.

Usage:
    chatfs-chatgpt-index-browse --cache <dir>

stdout: one /backend-api/conversations page per line (jsonl).
"""
from pathlib import Path

from chatfs.layout import DATA_DIR_NAME
from chatfs.provider.chatgpt.pluck import pluck_index_pages
from chatfs.shell.capture import browse, dump_jsonl

URL = "https://chatgpt.com"


def main() -> None:
    import sys

    match sys.argv[1:]:
        case ["--cache", cache]:
            root = Path(cache)
        case _:
            print(f"usage: {sys.argv[0]} --cache <dir>", file=sys.stderr)
            sys.exit(2)

    cdp = root / DATA_DIR_NAME / "index.cdp.jsonl"  # debug intermediate
    cdp.parent.mkdir(parents=True, exist_ok=True)
    browse(URL, cdp)
    with cdp.open() as f:
        dump_jsonl(pluck_index_pages(f), sys.stdout)


if __name__ == "__main__":
    main()
