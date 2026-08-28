#!/usr/bin/env python3
"""Render a conversation to markdown on stdout, whichever provider owns it.

Usage:
    chatfs-conversation-render <path-to-chat-dir-or-inside>

Resolves the provider from the cache segment the path sits under and runs
that provider's own `conversation render`, forwarding the path untouched.
The leaf's stdout is this command's stdout -- `run_leaf` leaves the child's
handles alone, so the markdown streams through rather than being buffered.
"""
from chatfs.conversation.dispatch import provider_for_path, run_leaf


def main() -> None:
    import sys

    argv = sys.argv[1:]
    if len(argv) != 1:
        print(f"usage: {sys.argv[0]} <path-to-chat-dir-or-inside>", file=sys.stderr)
        sys.exit(2)

    run_leaf(provider_for_path(argv[0]), "render", argv)
