#!/usr/bin/env python3
"""Render a conversation by URL, whichever provider serves it.

Usage:
    chatfs-conversation-url-render --cache <dir> <url>

Resolves the provider from the URL's host and runs that provider's own
`conversation url render`, forwarding every argument untouched.
"""
from chatfs.conversation.dispatch import provider_for_url, run_leaf, url_in


def main() -> None:
    import sys

    argv = sys.argv[1:]
    url = url_in(argv)
    if url is None:
        print(f"usage: {sys.argv[0]} --cache <dir> <url>", file=sys.stderr)
        sys.exit(2)

    run_leaf(provider_for_url(url), "url_render", argv)
