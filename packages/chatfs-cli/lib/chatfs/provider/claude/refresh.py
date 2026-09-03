#!/usr/bin/env python3
"""Refresh the claude.ai cache: index it, then capture what changed.

Usage:
    chatfs-provider-claude-refresh [--cache <dir>] <days>

Runs `index`, keeps the chats claude.ai says changed within the last
`<days>`, and captures the ones whose local capture predates that
change. Every capture still opens a window and waits for **Done
Capturing** -- what this removes is deciding which chats are worth the
click, not the clicking.

stdout: one placement record per conversation actually refreshed.
Exits 3 when the captured index doesn't reach back past the window,
before opening anything.
"""
from chatfs.cli import cache_root, extract_cache
from chatfs.provider.claude.layout import PROVIDER
from chatfs.refresh import day_count
from chatfs.shell.refresh import refresh_provider


def main() -> None:
    import os
    import sys
    from datetime import UTC, datetime

    root, rest = extract_cache(sys.argv[1:], os.environ, PROVIDER)
    days = day_count(rest)
    if root is None or days is None:
        print(f"usage: {sys.argv[0]} [--cache <dir>] <days>", file=sys.stderr)
        sys.exit(2)

    sys.exit(
        refresh_provider(PROVIDER, cache_root(root, PROVIDER), days, datetime.now(UTC))
    )


if __name__ == "__main__":
    main()
