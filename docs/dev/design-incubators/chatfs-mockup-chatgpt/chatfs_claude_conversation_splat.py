#!/usr/bin/env python3
"""Splat a claude conversation JSON into a `messages/` directory.

Input: path to conversation.json (the plucked
`/chat_conversations/{id}?…` response body).

Output: `<src>.splat/messages/<basename>.{json,md}` per message in
`chat_messages`. The .json carries the raw message object; the .md
carries the rendered content.

Scope: `text` blocks pass through; `thinking`, `tool_use`, and
`tool_result` blocks render as collapsible `<details type="...">`
sections (the `type` attribute makes each kind greppable). The raw
block stays in the .json regardless. No `conversations/`
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


def fenced_json(value: object) -> str:
    return "```json\n" + json.dumps(value, indent=2) + "\n```"


def render_details(kind: str, emoji: str, label: str, body: str) -> str:
    """Wrap non-answer content in a collapsible `<details>`, tagged for grep.

    `type="{kind}"` makes each block kind searchable (e.g.
    `grep 'type="tool_use"'`). `<details>` (vs a blockquote) keeps the
    content collapsed-by-default and avoids colliding with the render
    step's blockquote-as-fork-depth convention.
    """
    return (
        f'<details type="{kind}"><summary>{emoji} {label}</summary>'
        f"\n\n{body}\n\n</details>"
    )


def render_thinking(block: dict) -> str:
    """Render a `thinking` block. Claude's own `summaries` label the disclosure."""
    label = "; ".join(
        s["summary"] for s in block.get("summaries", []) if s.get("summary")
    )
    return render_details("thinking", "💭", label or "Thinking", block["thinking"].strip())


def render_tool_use(block: dict) -> str:
    """Render a `tool_use` block: friendly `message` as label, input as JSON."""
    name = block.get("name", "tool")
    message = block.get("message")
    label = f"{name} — {message}" if message else name
    return render_details("tool_use", "🔧", label, fenced_json(block.get("input", {})))


def render_result_content(content: object) -> str:
    """Render a tool_result `content` payload to markdown.

    Knowledge items (web search/fetch) become a link list; text items
    pass through; anything else falls back to JSON for fidelity.
    """
    if isinstance(content, str):
        return content.strip()
    if not isinstance(content, list):
        return fenced_json(content)
    lines: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            lines.append(str(item))
        elif item.get("text"):
            lines.append(item["text"].strip())
        elif item.get("title"):
            url = item.get("url")
            title = item["title"]
            lines.append(f"- [{title}]({url})" if url else f"- {title}")
        else:
            lines.append(fenced_json(item))
    return "\n".join(lines)


def render_tool_result(block: dict) -> str:
    """Render a `tool_result` block; flag errors in the label."""
    name = block.get("name", "tool")
    label = f"{name} result" + (" — ERROR" if block.get("is_error") else "")
    return render_details("tool_result", "📄", label, render_result_content(block.get("content")))


def extract_text(content_blocks: list[dict]) -> str:
    """Render content blocks to markdown, in document order.

    `text` passes through; `thinking`/`tool_use`/`tool_result` become
    collapsible `<details>`. Order is preserved so reasoning and tool
    calls sit where they happened, around the answer they produced.
    """
    pieces: list[str] = []
    for b in content_blocks:
        block_type = b.get("type")
        if block_type == "text" and b.get("text"):
            pieces.append(b["text"])
        elif block_type == "thinking" and b.get("thinking"):
            pieces.append(render_thinking(b))
        elif block_type == "tool_use":
            pieces.append(render_tool_use(b))
        elif block_type == "tool_result":
            pieces.append(render_tool_result(b))
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
