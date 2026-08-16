#!/usr/bin/env python3
"""Splat a ChatGPT export JSON into messages/ and conversations/ directories.

Output defaults to `<src>.splat/{messages,conversations}/`; an optional
second argv gives an explicit output-dir instead. Only the two owned
subdirs are cleared/recreated -- sibling content in an explicit
output-dir (e.g. a caller-placed `.data` symlink) is left alone."""

import os
import shutil
import sys
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import override

from . import json
from .json import JsonObj, JsonValue

MARKDOWN_PLACEHOLDER = "$MARKDOWN"


def fenced_json(value: JsonValue) -> str:
    return "```json\n" + json.dumps(value, indent=2) + "\n```"


def render_details(kind: str, icon: str, label: str, body: str, tool: str | None = None) -> str:
    """Wrap non-answer content in a collapsible `<details>`, tagged for grep.

    `type="{kind}"` mirrors claude/aistudio's splat so `grep 'type="thinking"'`
    or `grep 'type="tool_call"'` spans every provider; `tool="{tool}"` further
    distinguishes tool calls by name, matching claude's attribute.
    """
    tool_attr = f' tool="{tool}"' if tool else ""
    return (
        f'<details type="{kind}"{tool_attr}><summary>{icon} {label}</summary>'
        f"\n\n{body}\n\n</details>"
    )


@dataclass
class Message:
    """A parsed message from the ChatGPT export."""

    uuid: str
    timestamp: Decimal
    role: str
    text_content: str | None
    raw: JsonObj  # original JSON node

    @property
    def content_type(self) -> str:
        inner = self.raw.get("message")
        if inner is None:
            return "root"
        assert isinstance(inner, Mapping), inner
        content = inner.get("content")
        if content is None:
            return "null"
        assert isinstance(content, Mapping), content
        ct = content.get("content_type")
        if ct is None:
            return "null"
        assert isinstance(ct, str), ct
        return ct

    @override
    def __str__(self) -> str:
        ts_str = format_timestamp(self.timestamp)
        return f"{ts_str}.{self.role}.{self.uuid}.{self.content_type}"

    def write(self, messages_dir: Path) -> None:
        """Write this message's .json and optional .md to messages_dir."""
        basename = str(self)
        prepared = prepare_message(self.raw)
        with (messages_dir / f"{basename}.json").open("w") as f:
            json.dump(prepared, f, indent=2)
            _ = f.write("\n")
        if self.text_content is not None:
            _ = (messages_dir / f"{basename}.md").write_text(self.text_content + "\n")


@dataclass
class ConversationLink:
    """An entry in the conversation tree: a single message at a sequence position."""

    path: tuple[str, ...]  # dir components relative to conversations/
    seq: int
    message: Message

    @property
    def role(self) -> str:
        return self.message.role

    @property
    def content_type(self) -> str:
        return self.message.content_type

    @override
    def __str__(self) -> str:
        return f"{self.seq:03d}.{self.role}.{self.content_type}"

    def write(self, conversations_dir: Path, messages_dir: Path) -> None:
        """Write this link to the filesystem."""
        conv_dir = conversations_dir / Path(*self.path) if self.path else conversations_dir
        conv_dir.mkdir(parents=True, exist_ok=True)
        link_name = str(self)
        basename = str(self.message)
        rel_messages = os.path.relpath(messages_dir, conv_dir)
        (conv_dir / f"{link_name}.json").symlink_to(f"{rel_messages}/{basename}.json")
        if self.message.text_content is not None:
            (conv_dir / f"{link_name}.md").symlink_to(f"{rel_messages}/{basename}.md")


def load_conversation(path: Path) -> JsonObj:
    with path.open() as f:
        result = json.load(f)
    assert isinstance(result, Mapping), type(result)
    return result


def format_timestamp(unix_ts: Decimal | str) -> str:
    """Format timestamp as ISO 8601 with nanoseconds, like `date -Ins`."""
    unix_ts = Decimal(unix_ts)
    dt = datetime.fromtimestamp(int(unix_ts), tz=timezone.utc).astimezone()
    fractional = f"{unix_ts % 1:.9f}"[2:]  # nanoseconds
    return dt.strftime(f"%Y-%m-%dT%H:%M:%S,{fractional}%z")


def build_tree(mapping: JsonObj) -> dict[str, list[str]]:
    """Return {parent_id: [child_ids]} for tree traversal."""
    tree: dict[str, list[str]] = {}
    for msg_id, msg in mapping.items():
        assert isinstance(msg, Mapping), (msg_id, msg)
        parent = msg.get("parent")
        if parent is not None:
            assert isinstance(parent, str), parent
            tree.setdefault(parent, []).append(msg_id)
    return tree


def compute_min_timestamp(mapping: JsonObj) -> Decimal:
    """Find the earliest non-null timestamp across all messages."""
    timestamps: list[Decimal] = []
    for msg in mapping.values():
        assert isinstance(msg, Mapping), msg
        inner = msg.get("message")
        if inner is None:
            continue
        assert isinstance(inner, Mapping), inner
        create_time = inner.get("create_time")
        if create_time is not None:
            assert isinstance(create_time, (int, Decimal)), create_time
            timestamps.append(Decimal(create_time))
    return min(timestamps) if timestamps else Decimal(0)


def _extract_text_parts(content: JsonObj) -> str | None:
    """Extract from content_type=text: join non-None parts."""
    parts = content.get("parts", [])
    assert isinstance(parts, list), parts
    if not parts:
        return None
    filtered: list[str] = []
    for p in parts:
        if p is not None:
            assert isinstance(p, str), p
            filtered.append(p)
    if not filtered:
        return None
    return "\n".join(filtered)


def _extract_thoughts(content: JsonObj) -> str | None:
    """Extract from content_type=thoughts: join thought content blocks."""
    thoughts = content.get("thoughts", [])
    assert isinstance(thoughts, list), thoughts
    sections: list[str] = []
    for thought in thoughts:
        assert isinstance(thought, Mapping), thought
        text = thought.get("content")
        if text is not None:
            assert isinstance(text, str), text
            if text.strip():
                sections.append(text)
    if not sections:
        return None
    return "\n\n".join(sections)


def _extract_code(content: JsonObj) -> str | None:
    """Extract from content_type=code: wrap text in a fenced code block."""
    text = content.get("text")
    if text is None:
        return None
    assert isinstance(text, str), text
    if not text.strip():
        return None
    lang = content.get("language", "")
    assert isinstance(lang, str), lang
    return f"```{lang}\n{text}\n```"


def _extract_execution_output(content: JsonObj) -> str | None:
    """Extract from content_type=execution_output: wrap text in a fenced code block."""
    text = content.get("text")
    if text is None:
        return None
    assert isinstance(text, str), text
    if not text.strip():
        return None
    return f"```\n{text}\n```"


def _extract_multimodal_text(content: JsonObj) -> str | None:
    """Extract from content_type=multimodal_text: parts mix strings and
    image_asset_pointer dicts. Strings pass through; image parts become a
    placeholder carrying `asset_pointer`, since the image bytes aren't in
    the capture. Order is preserved so nothing is silently dropped."""
    parts = content.get("parts", [])
    assert isinstance(parts, list), parts
    rendered: list[str] = []
    for p in parts:
        if p is None:
            continue
        if isinstance(p, str):
            rendered.append(p)
            continue
        assert isinstance(p, Mapping), p
        pointer = p.get("asset_pointer")
        assert isinstance(pointer, str), pointer
        rendered.append(f"[image: {pointer}]")
    if not rendered:
        return None
    return "\n\n".join(rendered)


def _extract_reasoning_recap(content: JsonObj) -> str | None:
    """Extract from content_type=reasoning_recap."""
    text = content.get("content")
    if text is None:
        return None
    assert isinstance(text, str), text
    if not text.strip():
        return None
    return text


def _extract_tether_browsing_display(content: JsonObj) -> str | None:
    """Extract from content_type=tether_browsing_display: legacy ChatGPT
    browsing-tool result display. `result`/`summary` are the only text-bearing
    fields observed; render whichever is non-empty, joined if both are."""
    parts = [
        text
        for text in (content.get("result"), content.get("summary"))
        if isinstance(text, str) and text.strip()
    ]
    if not parts:
        return None
    return "\n\n".join(parts)


def _extract_editable_context(content: JsonObj) -> str | None:
    """Extract from user_editable_context or model_editable_context."""
    for key in ("user_instructions", "user_profile", "model_set_context"):
        val = content.get(key)
        if val is not None:
            assert isinstance(val, str), val
            if val.strip():
                return val
    return None


def _extract_tool_metadata(message: JsonObj) -> str | None:
    """Extract tool results from message metadata (search queries/results)."""
    metadata = message.get("metadata")
    if metadata is None:
        return None
    assert isinstance(metadata, Mapping), metadata

    sections: list[str] = []

    queries = metadata.get("search_model_queries")
    if queries is not None:
        assert isinstance(queries, Mapping), queries
        q_list = queries.get("queries", [])
        assert isinstance(q_list, list), q_list
        if q_list:
            lines: list[str] = []
            for q in q_list:
                assert isinstance(q, str), q
                lines.append(f"- {q}")
            sections.append("## Queries\n" + "\n".join(lines))

    groups = metadata.get("search_result_groups")
    if groups is not None:
        assert isinstance(groups, list), groups
        for group in groups:
            assert isinstance(group, Mapping), group
            domain = group.get("domain", "?")
            assert isinstance(domain, str), domain
            entries = group.get("entries", [])
            assert isinstance(entries, list), entries
            lines = [f"## {domain}"]
            for entry in entries:
                assert isinstance(entry, Mapping), entry
                url = entry.get("url", "")
                assert isinstance(url, str), url
                title = entry.get("title", "")
                assert isinstance(title, str), title
                lines.append(f"- [{title}]({url})")
            sections.append("\n".join(lines))

    if not sections:
        return None
    return "\n\n".join(sections)


def extract_text_content(raw: JsonObj) -> str | None:
    """Extract renderable text from a raw message node, if present.

    A node with no `message` or no `content` legitimately has nothing to
    render (e.g. the root node). But once a `content_type` is present, an
    unrecognized one renders as a raw-JSON `<details type="unmodeled">`
    rather than vanishing or crashing the render — mirrors claude's
    `extract_text` for unknown block types: the export format is a third
    party's and unversioned, so a fresh content_type is expected drift.

    Reasoning (`thoughts`, `reasoning_recap`) and tool content (`code`,
    `execution_output`, tool-role search metadata) render inside a
    collapsible `<details type="thinking"|"tool_call">`, matching
    claude/aistudio's splat — so `grep 'type="thinking"'` finds every
    provider's reasoning instead of silently missing chatgpt's bare
    markdown. `multimodal_text` (mixed image/string parts) renders like
    `text`: verbatim, no `<details>` wrapper, since it's a real user turn.
    """
    inner = raw.get("message")
    if inner is None:
        return None
    assert isinstance(inner, Mapping), inner
    content = inner.get("content")
    if content is None:
        return None
    assert isinstance(content, Mapping), content
    content_type = content.get("content_type")

    if content_type == "text":
        # For tool messages, text parts may be empty; check metadata too
        text = _extract_text_parts(content)
        if text is not None and text.strip():
            return text
        author = inner.get("author")
        if isinstance(author, Mapping) and author.get("role") == "tool":
            meta = _extract_tool_metadata(inner)
            if meta is None:
                return None
            return render_details("tool_call", "🔍", "Search", meta, tool="search")
        return None
    elif content_type == "multimodal_text":
        return _extract_multimodal_text(content)
    elif content_type == "thoughts":
        thoughts = _extract_thoughts(content)
        if thoughts is None:
            return None
        return render_details("thinking", "💭", "Thinking", thoughts)
    elif content_type == "code":
        code = _extract_code(content)
        if code is None:
            return None
        recipient = inner.get("recipient")
        tool = recipient if isinstance(recipient, str) and recipient != "all" else None
        return render_details("tool_call", "🛠️", tool or "Code", code, tool=tool)
    elif content_type == "execution_output":
        output = _extract_execution_output(content)
        if output is None:
            return None
        return render_details("tool_call", "🛠️", "Output", output)
    elif content_type == "reasoning_recap":
        recap = _extract_reasoning_recap(content)
        if recap is None:
            return None
        return render_details("thinking", "💭", "Reasoning recap", recap)
    elif content_type in ("user_editable_context", "model_editable_context"):
        return _extract_editable_context(content)
    elif content_type == "tether_browsing_display":
        display = _extract_tether_browsing_display(content)
        if display is None:
            return None
        return render_details("tool_call", "🛠️", "Browsing result", display)
    else:
        print(
            f"warning: unmodeled content_type, passed through: {content_type!r}",
            file=sys.stderr,
        )
        return render_details(
            "unmodeled", "❓", f"Unrecognized content: {content_type}", fenced_json(content)
        )


def parse_messages(mapping: JsonObj, min_ts: Decimal) -> dict[str, Message]:
    """Parse raw JSON mapping into Message objects."""
    messages: dict[str, Message] = {}
    for msg_id, raw in mapping.items():
        assert isinstance(raw, Mapping), (msg_id, raw)
        inner = raw.get("message")
        if inner is None:
            timestamp = min_ts
            role = "root"
        else:
            assert isinstance(inner, Mapping), inner
            create_time = inner.get("create_time")
            if create_time is not None:
                assert isinstance(create_time, (int, Decimal)), create_time
                timestamp = Decimal(create_time)
            else:
                timestamp = min_ts
            author = inner.get("author")
            if author is None:
                role = "unknown"
            else:
                assert isinstance(author, Mapping), author
                role = author.get("role", "unknown")
                assert isinstance(role, str), role
        messages[msg_id] = Message(
            uuid=msg_id,
            timestamp=timestamp,
            role=role,
            text_content=extract_text_content(raw),
            raw=raw,
        )
    return messages


def find_roots(mapping: JsonObj) -> list[str]:
    """Find messages with no parent (roots of the tree)."""
    roots: list[str] = []
    for msg_id, msg in mapping.items():
        assert isinstance(msg, Mapping), (msg_id, msg)
        if msg.get("parent") is None:
            roots.append(msg_id)
    return roots


def _sorted_children(
    tree: dict[str, list[str]],
    messages: dict[str, Message],
    msg: Message,
) -> list[Message]:
    return sorted(
        [messages[c] for c in tree.get(msg.uuid, [])],
        key=lambda c: c.timestamp,
    )


def assert_unique(items: list[object], label: str = "") -> None:
    assert len(set(items)) == len(items), f"Duplicate in {label}: {items}"


def _child_links(
    messages: dict[str, Message],
    tree: dict[str, list[str]],
    parent: ConversationLink,
) -> Iterator[ConversationLink]:
    """Given a link, return the next links to process."""
    next_children = _sorted_children(tree, messages, parent.message)
    assert_unique(
        [m.timestamp for m in next_children],
        f"timestamps at seq {parent.seq + 1}",
    )
    is_fork = len(next_children) > 1
    for child in reversed(next_children):
        if is_fork:
            link = ConversationLink(parent.path, parent.seq + 1, child)
            ts = format_timestamp(child.timestamp)
            path = parent.path + (f"{link}.{ts}",)
        else:
            path = parent.path
        yield ConversationLink(path, parent.seq + 1, child)


def enumerate_conversation_links(
    messages: dict[str, Message],
    tree: dict[str, list[str]],
    root: str,
) -> Iterator[ConversationLink]:
    """Stack-based enumeration of conversation tree as ConversationLinks."""
    stack = [ConversationLink((), 0, messages[root])]
    while stack:
        link = stack.pop()
        yield link
        stack.extend(_child_links(messages, tree, link))


def prepare_message(raw: JsonObj) -> JsonObj:
    """Return raw node with text parts replaced by MARKDOWN_PLACEHOLDER, or unchanged.

    Only replaces when content_type is 'text' and parts contain actual text,
    since that's the only case where .md content comes from parts[].
    """
    inner = raw.get("message")
    if inner is None:
        return raw
    assert isinstance(inner, Mapping), inner
    content = inner.get("content")
    if content is None:
        return raw
    assert isinstance(content, Mapping), content
    if content.get("content_type") != "text":
        return raw
    parts = content.get("parts", [])
    assert isinstance(parts, list), parts
    if not any(isinstance(p, str) and p.strip() for p in parts):
        return raw
    return {**raw, "message": {**inner, "content": {**content, "parts": [MARKDOWN_PLACEHOLDER]}}}


def main() -> None:
    if len(sys.argv) not in (2, 3):
        print(f"Usage: {sys.argv[0]} <chatgpt-export.json> [output-dir]", file=sys.stderr)
        sys.exit(1)

    src = Path(sys.argv[1])
    data = load_conversation(src)

    mapping = data["mapping"]
    assert isinstance(mapping, Mapping), type(mapping)
    tree = build_tree(mapping)
    root = find_roots(mapping)
    assert len(root) == 1, f"Expected 1 root, got {len(root)}: {root}"
    root = root[0]

    base_dir = Path(sys.argv[2]) if len(sys.argv) == 3 else src.with_suffix(".splat")
    messages_dir = base_dir / "messages"
    conversations_dir = base_dir / "conversations"

    # Clean up previous run's outputs (script owns these two subdirs, not
    # base_dir itself)
    if messages_dir.exists():
        shutil.rmtree(messages_dir)
    if conversations_dir.exists():
        shutil.rmtree(conversations_dir)

    min_ts = compute_min_timestamp(mapping)
    messages = parse_messages(mapping, min_ts)

    # Write all messages
    messages_dir.mkdir(parents=True, exist_ok=True)
    for msg in messages.values():
        msg.write(messages_dir)

    # Write conversation tree
    conversations_dir.mkdir(parents=True, exist_ok=True)
    for link in enumerate_conversation_links(messages, tree, root):
        link.write(conversations_dir, messages_dir)

    print(f"Wrote {len(messages)} messages to {base_dir}")


if __name__ == "__main__":
    main()
