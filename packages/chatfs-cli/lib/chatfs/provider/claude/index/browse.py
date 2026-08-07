#!/usr/bin/env python3
"""Capture claude.ai's conversation index.

Usage:
    chatfs-claude-index-browse --cache <dir>

stdout: one index entry page per line (jsonl) — pluck flattens every
`/chat_conversations_v2` response the browse session sees, so this catches
as many pages as har-browse's session actually triggers. This account's
chats fit one page in practice; a scroll-triggered second page is
unverified here (same har-browse "wait until has_more=false" gap tracked
for claude in todo.md).
"""
from pathlib import Path

from chatfs.layout import DATA_DIR_NAME
from chatfs.provider.claude.pluck import pluck_index_pages
from chatfs.shell.capture import browse, dump_jsonl

URL = "https://claude.ai/recents"


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
