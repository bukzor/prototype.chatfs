#!/usr/bin/env python3
"""Splat a claude conversation JSON into a `messages/` directory.

Input: path to conversation.json (the plucked
`/chat_conversations/{id}?…` response body).

Output: `<src>.splat/messages/<basename>.{json,md}` per message in
`chat_messages`. The .json carries the raw message object; the .md
carries the rendered text and thinking content.

Scope: `text` and `thinking` blocks render to the .md (thinking as a
collapsible `<details>`); `tool_use`/`tool_result` blocks are skipped
from the .md but preserved in the .json. No `conversations/`
branch-symlinks yet (next ladder rung).
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


def render_thinking(block: dict) -> str:
    """Render a `thinking` block as a collapsible `<details>`.

    Claude's own `summaries[].summary` headers label the disclosure, so
    the collapsed view stays scannable; the raw `thinking` text is the
    body. `<details>` (vs a blockquote) avoids colliding with the render
    step's blockquote-as-fork-depth convention.
    """
    label = "; ".join(
        s["summary"] for s in block.get("summaries", []) if s.get("summary")
    )
    text = block["thinking"].strip()
    return f"<details><summary>💭 {label or 'Thinking'}</summary>\n\n{text}\n\n</details>"


def extract_text(content_blocks: list[dict]) -> str:
    """Render `text` and `thinking` blocks to markdown, in document order.

    `text` blocks pass through; `thinking` blocks become collapsible
    `<details>` sections. Order is preserved so reasoning precedes the
    answer it produced. `tool_use`/`tool_result` remain out of scope.
    """
    pieces: list[str] = []
    for b in content_blocks:
        block_type = b.get("type")
        if block_type == "text" and b.get("text"):
            pieces.append(b["text"])
        elif block_type == "thinking" and b.get("thinking"):
            pieces.append(render_thinking(b))
    return "\n\n".join(pieces)


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

    rendered_count = 0
    for msg in chat_messages:
        basename = basename_for(msg)
        (messages_dir / f"{basename}.json").write_text(
            json.dumps(msg, indent=2) + "\n"
        )
        text = extract_text(msg["content"])
        if text:
            (messages_dir / f"{basename}.md").write_text(text + "\n")
            rendered_count += 1

    print(
        f"wrote {len(chat_messages)} message(s), {rendered_count} with rendered "
        f"content, to {base_dir}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
