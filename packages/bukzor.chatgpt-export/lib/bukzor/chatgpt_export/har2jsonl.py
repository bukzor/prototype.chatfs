#!/usr/bin/env python3
"""Extract ChatGPT conversations from HAR files to JSONL."""

import base64
import json
import re
import sys
from collections.abc import Iterator
from pathlib import Path

CONVERSATION_URL_PATTERN = re.compile(r"/backend-api/conversation/[0-9a-f-]+$")


def is_conversation_entry(entry: dict) -> bool:
    """Check if HAR entry is a conversation fetch."""
    url = entry.get("request", {}).get("url", "")
    return bool(CONVERSATION_URL_PATTERN.search(url))


def decode_response_body(content: dict) -> str:
    """Decode HAR response content, handling base64 encoding."""
    text = content.get("text", "")
    if content.get("encoding") == "base64":
        return base64.b64decode(text).decode("utf-8")
    return text


def extract_conversations(har: dict) -> Iterator[dict]:
    """Yield conversation JSON objects from HAR data."""
    entries = har.get("log", {}).get("entries", [])
    for entry in entries:
        if not is_conversation_entry(entry):
            continue
        content = entry.get("response", {}).get("content", {})
        body = decode_response_body(content)
        if body:
            yield json.loads(body)


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <chatgpt.har>", file=sys.stderr)
        sys.exit(1)

    src = Path(sys.argv[1])
    dest = src.with_suffix(".json")

    with src.open() as f:
        har = json.load(f)

    conversations = list(extract_conversations(har))

    with dest.open("w") as f:
        json.dump(conversations[0], f)

    print(f"Wrote {dest}", file=sys.stderr)
    print(dest)

    assert len(conversations) == 1, f"Expected 1 conversation, got {len(conversations)}"


if __name__ == "__main__":
    main()
