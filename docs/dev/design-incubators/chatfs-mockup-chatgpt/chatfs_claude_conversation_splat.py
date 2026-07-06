#!/usr/bin/env python3
"""Splat a claude conversation JSON into a `messages/` directory.

Input: path to conversation.json (the plucked
`/chat_conversations/{id}?…` response body).

Output: `<src>.splat/messages/<basename>.{json,md}` per message in
`chat_messages`. The .json carries the raw message object; the .md
carries the rendered content.

Scope: `text` blocks pass through; `thinking` and each
`tool_use`+`tool_result` pair render as collapsible
`<details type="...">` sections (the `type` attribute makes each kind
greppable). Unknown block types raise. The raw block stays in the
.json regardless. No `conversations/` branch-symlinks yet (next ladder
rung).
"""
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

import chatfs_json
from chatfs_claude_layout import safe_filename
from chatfs_claude_types import (
    ChatMessage,
    ContentBlock,
    Several,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    is_conversation,
)
from chatfs_json import JsonValue


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
    return "```json\n" + json.dumps(value, indent=2, ensure_ascii=False) + "\n```"


def render_details(
    kind: str, icon: str, label: str, body: str, tool: str | None = None
) -> str:
    """Wrap non-answer content in a collapsible `<details>`, tagged for grep.

    `type="{kind}"` makes each block kind searchable (e.g.
    `grep 'type="tool_call"'`); `tool="{tool}"` further distinguishes
    tool calls by name. `<details>` (vs a blockquote) keeps the content
    collapsed-by-default and avoids colliding with the render step's
    blockquote-as-fork-depth convention.
    """
    tool_attr = f' tool="{tool}"' if tool else ""
    return (
        f'<details type="{kind}"{tool_attr}><summary>{icon} {label}</summary>'
        f"\n\n{body}\n\n</details>"
    )


def render_thinking(block: ThinkingBlock) -> str:
    """Render a `thinking` block. Claude's own `summaries` label the disclosure."""
    label = "; ".join(s["summary"] for s in block["summaries"])
    return render_details("thinking", "💭", label or "Thinking", block["thinking"].strip())


def render_result_content(content: JsonValue) -> str:
    """Render a tool_result `content` payload to markdown.

    Tool result schemas are open-ended (each tool returns its own item
    shape), so this dispatches on the item keys it knows — knowledge
    items (web search/fetch) become a link list, text items pass
    through — and falls back to JSON for anything unrecognized rather
    than dropping it.
    """
    match content:
        case str():
            return content.strip()
        case list():
            lines: list[str] = []
            for item in content:
                if not isinstance(item, dict):
                    lines.append(str(item))
                elif isinstance(text := item.get("text"), str) and text:
                    lines.append(text.strip())
                elif isinstance(title := item.get("title"), str):
                    url = item.get("url")
                    lines.append(f"- [{title}]({url})" if isinstance(url, str) else f"- {title}")
                else:
                    lines.append(fenced_json(item))
            return "\n".join(lines)
        case _:
            return fenced_json(content)


def render_tool_call(use: ToolUseBlock, result: ToolResultBlock) -> str:
    """Render a `tool_use` + its `tool_result` as one collapsible pair.

    Every tool_use is immediately followed by the tool_result for the
    same call (asserted by the caller), so they read better fused: one
    disclosure tagged `tool="<name>"`. web_search/web_fetch get a
    bespoke icon and a summary built from their single argument, with
    the request omitted; other tools show the request JSON above the
    result.
    """
    name = use["name"]
    tool_input = use["input"]
    result_md = render_result_content(result["content"])
    error = " — ERROR" if result["is_error"] else ""

    match name:
        case "web_search":
            assert set(tool_input) == {"query"}, tool_input
            query = tool_input["query"]
            assert isinstance(query, str), query
            label = query + error
            return render_details("tool_call", "🔍", label, result_md, tool=name)
        case "web_fetch":
            assert set(tool_input) == {"url"}, tool_input
            url = tool_input["url"]
            assert isinstance(url, str), url
            label = url + error
            return render_details("tool_call", "🕷️", label, result_md, tool=name)
        case _:
            label = f"{name} — {use['message']}" + error
            body = (
                f"**Request:**\n\n{fenced_json(tool_input)}\n\n"
                f"**Result:**\n\n{result_md}"
            )
            return render_details("tool_call", "🛠️", label, body, tool=name)


def extract_text(content_blocks: Several[ContentBlock]) -> str:
    """Render content blocks to markdown, in document order.

    `text` passes through; `thinking` and each tool_use+tool_result
    pair become collapsible `<details>`. Order is preserved so
    reasoning and tool calls sit where they happened, around the answer
    they produced. Unknown block types raise rather than vanish.
    """
    pieces: list[str] = []
    i = 0
    while i < len(content_blocks):
        block = content_blocks[i]
        match block:
            case {"type": "text", "text": text}:
                if text:  # empty text blocks occur; skip them
                    pieces.append(text)
            case {"type": "thinking"}:
                pieces.append(render_thinking(block))
            case {"type": "tool_use"}:
                next_block = content_blocks[i + 1]  # each tool_use is paired next
                match next_block:
                    case {"type": "tool_result"}:
                        assert next_block["tool_use_id"] == block["id"], (block, next_block)
                        pieces.append(render_tool_call(block, next_block))
                    case _:
                        raise AssertionError(
                            ("tool_use without following tool_result", block, next_block)
                        )
                i += 1  # consume the paired tool_result
            case {"type": "tool_result"}:
                raise AssertionError(("tool_result without preceding tool_use", block))
            case _:
                raise ValueError(f"unexpected content type: {block['type']!r}")
        i += 1
    return "\n\n".join(pieces)


def basename_for(msg: ChatMessage) -> str:
    return safe_filename(
        f"{format_timestamp(msg['created_at'])}.{msg['sender']}.{msg['uuid']}"
    )


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <conversation.json>", file=sys.stderr)
        sys.exit(1)

    src = Path(sys.argv[1])
    doc = chatfs_json.loads(src.read_text())
    assert is_conversation(doc), doc
    chat_messages = doc["chat_messages"]

    base_dir = src.with_suffix(".splat")
    messages_dir = base_dir / "messages"
    if base_dir.exists():
        shutil.rmtree(base_dir)
    messages_dir.mkdir(parents=True)

    rendered_count = 0
    for msg in chat_messages:
        basename = basename_for(msg)
        _ = (messages_dir / f"{basename}.json").write_text(
            json.dumps(msg, indent=2, ensure_ascii=False) + "\n"
        )
        text = extract_text(tuple(msg["content"]))
        if text:
            _ = (messages_dir / f"{basename}.md").write_text(text + "\n")
            rendered_count += 1

    print(
        f"wrote {len(chat_messages)} message(s), {rendered_count} with rendered "
        + f"content, to {base_dir}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
