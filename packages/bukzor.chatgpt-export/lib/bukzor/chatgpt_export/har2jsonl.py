#!/usr/bin/env python3
"""Extract ChatGPT conversations from HAR files to JSONL."""

import base64
import json
import re
import sys
from collections.abc import Iterator
from pathlib import Path

from .types import JsonObj

CONVERSATION_URL_PATTERN = re.compile(r"/backend-api/conversation/[0-9a-f-]+$")


def is_conversation_entry(entry: JsonObj) -> bool:
    """Check if HAR entry is a conversation fetch."""
    request = entry.get("request")
    if not isinstance(request, dict):
        return False
    url = request.get("url", "")
    assert isinstance(url, str), url
    return bool(CONVERSATION_URL_PATTERN.search(url))


def decode_response_body(content: JsonObj) -> str:
    """Decode HAR response content, handling base64 encoding."""
    text = content.get("text", "")
    assert isinstance(text, str), text
    if content.get("encoding") == "base64":
        return base64.b64decode(text).decode("utf-8")
    return text


def extract_conversations(har: JsonObj) -> Iterator[JsonObj]:
    """Yield conversation JSON objects from HAR data."""
    log = har.get("log")
    if not isinstance(log, dict):
        return
    entries = log.get("entries", [])
    assert isinstance(entries, list), entries
    for entry in entries:
        assert isinstance(entry, dict), entry
        if not is_conversation_entry(entry):
            continue
        response = entry.get("response")
        assert isinstance(response, dict), response
        content = response.get("content")
        assert isinstance(content, dict), content
        body = decode_response_body(content)
        if body:
            result = json.loads(body)
            assert isinstance(result, dict), type(result)
            yield result


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <chatgpt.har>", file=sys.stderr)
        sys.exit(1)

    src = Path(sys.argv[1])
    dest = src.with_suffix(".json")

    with src.open() as f:
        har = json.load(f)

    conversations = list(extract_conversations(har))
    assert len(conversations) == 1, f"Expected 1 conversation, got {len(conversations)}"

    with dest.open("w") as f:
        json.dump(conversations[0], f)

    print(f"Wrote {dest}", file=sys.stderr)
    print(dest)


if __name__ == "__main__":
    main()
