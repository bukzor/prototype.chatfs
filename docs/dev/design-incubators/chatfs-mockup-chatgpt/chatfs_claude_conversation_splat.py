#!/usr/bin/env python3
"""Splat a claude conversation JSON into a `messages/` directory.

Input: path to conversation.json (the plucked
`/chat_conversations/{id}?…` response body).

Output: `<src>.splat/messages/<basename>.{json,md}` per message in
`chat_messages`. The .json carries the raw message object; the .md
carries the concatenated text-block content.

MVP scope: text blocks only — `thinking`, `tool_use`, `tool_result`
content blocks are skipped from the .md but preserved in the .json.
No `conversations/` branch-symlinks yet (next ladder rung).
"""
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

from chatfs_claude_layout import safe_filename


def format_timestamp(created_at: str) -> str:
    """ISO 8601 in local TZ, comma fractional, +HHMM offset.

    Matches chatgpt-splat's basename timestamp so messages/<stem> links
    are readable side-by-side with the chatgpt side. Claude `created_at`
    has microsecond precision; we pad to 9 digits.
    """
    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00")).astimezone()
    fractional = f"{dt.microsecond:06d}000"
    return dt.strftime(f"%Y-%m-%dT%H:%M:%S,{fractional}%z")


def extract_text(content_blocks: list[dict]) -> str:
    """Concatenate `text` from `text`-typed content blocks. MVP scope."""
    return "\n\n".join(
        b["text"]
        for b in content_blocks
        if b.get("type") == "text" and b.get("text")
    )


def basename_for(msg: dict) -> str:
    return safe_filename(
        f"{format_timestamp(msg['created_at'])}.{msg['sender']}.{msg['uuid']}"
    )


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <conversation.json>", file=sys.stderr)
        sys.exit(1)

    src = Path(sys.argv[1])
    doc = json.loads(src.read_text())
    chat_messages = doc["chat_messages"]

    base_dir = src.with_suffix(".splat")
    messages_dir = base_dir / "messages"
    if base_dir.exists():
        shutil.rmtree(base_dir)
    messages_dir.mkdir(parents=True)

    text_count = 0
    for msg in chat_messages:
        basename = basename_for(msg)
        (messages_dir / f"{basename}.json").write_text(
            json.dumps(msg, indent=2) + "\n"
        )
        text = extract_text(msg["content"])
        if text:
            (messages_dir / f"{basename}.md").write_text(text + "\n")
            text_count += 1

    print(
        f"wrote {len(chat_messages)} message(s), {text_count} with text content, "
        f"to {base_dir}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
