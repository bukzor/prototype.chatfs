#!/usr/bin/env python3
"""Analyze a claude.ai conversation JSON for fork-related structure.

Usage:
    ./investigate-forks.py conversation.json
    ./investigate-forks.py < conversation.json

Input: one raw conversation object, as captured by the chatfs pipeline
(HAR capture -> splat) or saved from the claude.ai API any other way.
Prints the full structure, every fork-suggestive field path, and the
scalar metadata -- raw material for api-investigation.md (Phase 1 of
the fork-representation investigation).
"""

import json
import sys
from collections.abc import Iterator
from typing import cast

type JsonValue = None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]

FORK_KEYWORDS = ("fork", "parent", "branch", "ancestor", "child", "thread")


def fork_fields(obj: JsonValue, path: str = "") -> Iterator[tuple[str, JsonValue]]:
    """Yield (path, value) for every key containing a fork-suggestive word."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key
            if any(keyword in key.lower() for keyword in FORK_KEYWORDS):
                yield current_path, value
            yield from fork_fields(value, current_path)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            yield from fork_fields(item, f"{path}[{i}]")


def print_banner(title: str) -> None:
    print("=" * 80)
    print(title)
    print("=" * 80)


def main() -> None:
    if len(sys.argv) > 2:
        sys.exit(f"Usage: {sys.argv[0]} [conversation.json]  (default: stdin)")
    source = open(sys.argv[1]) if len(sys.argv) == 2 else sys.stdin
    with source as f:
        conversation = cast(JsonValue, json.load(f))
    assert isinstance(conversation, dict), type(conversation)

    print_banner("FULL RAW RESPONSE")
    print(json.dumps(conversation, indent=2))
    print()

    print_banner("FORK-RELATED FIELDS")
    for path, value in fork_fields(conversation):
        print(f"Found: {path} = {value}")

    print()
    print_banner("CONVERSATION METADATA")
    metadata = {k: v for k, v in conversation.items() if not isinstance(v, (dict, list))}
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
