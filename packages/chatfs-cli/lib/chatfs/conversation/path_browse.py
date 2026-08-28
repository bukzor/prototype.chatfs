#!/usr/bin/env python3
"""Browse a conversation by chat-dir address, whichever provider owns it.

Usage:
    chatfs-conversation-path-browse <path-to-chat-dir-or-inside>

Resolves the provider from the cache segment the path sits under and runs
that provider's own `conversation path browse`, forwarding the path
untouched.
"""
from chatfs.conversation.dispatch import provider_for_path, run_leaf


def main() -> None:
    import sys

    argv = sys.argv[1:]
    if len(argv) != 1:
        print(f"usage: {sys.argv[0]} <path-to-chat-dir-or-inside>", file=sys.stderr)
        sys.exit(2)

    run_leaf(provider_for_path(argv[0]), "path_browse", argv)
