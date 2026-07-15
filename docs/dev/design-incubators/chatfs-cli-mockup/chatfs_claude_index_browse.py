#!/usr/bin/env python3
"""Capture claude.ai's conversation index.

Usage:
    chatfs_claude_index_browse.py

stdout: one index entry page per line (jsonl) — pluck flattens every
`/chat_conversations_v2` response the browse session sees, so this catches
as many pages as har-browse's session actually triggers. This account's
chats fit one page in practice; a scroll-triggered second page is
unverified here (same har-browse "wait until has_more=false" gap tracked
for claude in todo.md).
"""
import sys
from pathlib import Path

from chatfs_claude_layout import pluck_index_pages
from chatfs_layout import browse, dump_jsonl

HERE = Path(__file__).parent
CDP = HERE / "claude.index.cdp.jsonl"  # debug intermediate

URL = "https://claude.ai/recents"


def main() -> None:
    browse(URL, CDP)
    with CDP.open() as f:
        dump_jsonl(pluck_index_pages(f), sys.stdout)


if __name__ == "__main__":
    main()
