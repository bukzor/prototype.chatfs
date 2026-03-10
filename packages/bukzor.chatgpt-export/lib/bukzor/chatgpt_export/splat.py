#!/usr/bin/env python3
"""Splat a ChatGPT export JSON into messages/ and conversations/ directories."""

import json
import os
import shutil
import sys
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from .types import JsonObj

MARKDOWN_PLACEHOLDER = "$MARKDOWN"


@dataclass
class Message:
    """A parsed message from the ChatGPT export."""

    uuid: str
    timestamp: Decimal
    role: str
    text_content: str | None
    raw: JsonObj  # original JSON node

    def __str__(self) -> str:
        ts_str = format_timestamp(self.timestamp)
        return f"{ts_str}.{self.role}.{self.uuid}"

    def write(self, messages_dir: Path) -> None:
        """Write this message's .json and optional .md to messages_dir."""
        basename = str(self)
        prepared = prepare_message(self.raw, self.text_content)
        with (messages_dir / f"{basename}.json").open("w") as f:
            json.dump(prepared, f, indent=2)
        if self.text_content:
            (messages_dir / f"{basename}.md").write_text(self.text_content)


@dataclass
class ConversationLink:
    """An entry in the conversation tree: one or more messages at a sequence position."""

    path: tuple[str, ...]  # dir components relative to conversations/
    seq: int
    messages: list[Message]

    @property
    def role(self) -> str:
        roles = set(m.role for m in self.messages)
        if len(roles) == 1:
            return next(iter(roles))
        return "fork"

    def __str__(self) -> str:
        return f"{self.seq:03d}.{self.role}"

    def write(self, conversations_dir: Path, messages_dir: Path) -> None:
        """Write this link to the filesystem."""
        conv_dir = conversations_dir / Path(*self.path) if self.path else conversations_dir
        conv_dir.mkdir(parents=True, exist_ok=True)
        link_name = str(self)

        if len(self.messages) == 1:
            # Single message: create symlinks
            msg = self.messages[0]
            basename = str(msg)
            rel_messages = os.path.relpath(messages_dir, conv_dir)
            (conv_dir / f"{link_name}.json").symlink_to(f"{rel_messages}/{basename}.json")
            if msg.text_content:
                (conv_dir / f"{link_name}.md").symlink_to(f"{rel_messages}/{basename}.md")
        else:
            # Fork: create directory with branch subdirectories
            fork_dir = conv_dir / link_name
            fork_dir.mkdir(parents=True, exist_ok=True)
            for msg in self.messages:
                (fork_dir / str(msg)).mkdir(parents=True, exist_ok=True)


def load_conversation(path: Path) -> JsonObj:
    with path.open() as f:
        result: JsonObj = json.load(f)
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


def compute_min_timestamp(mapping: JsonObj) -> float:
    """Find the earliest non-null timestamp across all messages."""
    timestamps: list[float] = []
    for msg in mapping.values():
        assert isinstance(msg, Mapping), msg
        inner = msg.get("message")
        if inner is None:
            continue
        assert isinstance(inner, Mapping), inner
        create_time = inner.get("create_time")
        if create_time:
            assert isinstance(create_time, (int, float)), create_time
            timestamps.append(float(create_time))
    return min(timestamps) if timestamps else 0.0


def extract_text_content(raw: JsonObj) -> str | None:
    """Extract text content from a raw message node, if present."""
    inner = raw.get("message")
    if inner is None:
        return None
    assert isinstance(inner, Mapping), inner
    content = inner.get("content")
    if content is None:
        return None
    assert isinstance(content, Mapping), content
    if content.get("content_type") != "text":
        return None
    parts = content.get("parts", [])
    assert isinstance(parts, list), parts
    if not parts:
        return None
    filtered = [str(p) for p in parts if p is not None]
    if not filtered:
        return None
    return "\n".join(filtered)


def parse_messages(mapping: JsonObj, min_ts: float) -> dict[str, Message]:
    """Parse raw JSON mapping into Message objects."""
    messages: dict[str, Message] = {}
    for msg_id, raw in mapping.items():
        assert isinstance(raw, Mapping), (msg_id, raw)
        inner = raw.get("message")
        if inner is None:
            timestamp = Decimal(str(min_ts))
            role = "root"
        else:
            assert isinstance(inner, Mapping), inner
            create_time = inner.get("create_time")
            if create_time:
                assert isinstance(create_time, (int, float)), create_time
                timestamp = Decimal(str(float(create_time)))
            else:
                timestamp = Decimal(str(min_ts))
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
    return [
        msg_id
        for msg_id, msg in mapping.items()
        if isinstance(msg, Mapping) and msg.get("parent") is None
    ]


def enumerate_conversation_links(
    msg_id: str,
    tree: dict[str, list[str]],
    messages: dict[str, Message],
    seq: int,
    path: tuple[str, ...],
) -> Iterator[ConversationLink]:
    """Pure recursive enumeration of conversation tree as ConversationLinks."""
    msg = messages[msg_id]
    children = sorted(
        tree.get(msg_id, []),
        key=lambda c: float(messages[c].timestamp),
    )

    if len(children) <= 1:
        # Leaf or linear: single-message link
        yield ConversationLink(path=path, seq=seq, messages=[msg])
        if children:
            yield from enumerate_conversation_links(
                children[0], tree, messages, seq + 1, path
            )
    else:
        # Fork: yield the current message, then yield the fork link
        yield ConversationLink(path=path, seq=seq, messages=[msg])
        fork_children = [messages[c] for c in children]
        fork_link = ConversationLink(path=path, seq=seq + 1, messages=fork_children)
        yield fork_link
        # Recurse into each branch
        fork_name = str(fork_link)
        for child in children:
            branch_name = str(messages[child])
            branch_path = path + (fork_name, branch_name)
            yield from enumerate_conversation_links(
                child, tree, messages, seq + 1, branch_path
            )


def prepare_message(raw: JsonObj, text_content: str | None) -> JsonObj:
    """Return raw node with text parts replaced by MARKDOWN_PLACEHOLDER, or unchanged."""
    if not text_content:
        return raw
    inner = raw["message"]
    assert isinstance(inner, Mapping), inner
    content = inner["content"]
    assert isinstance(content, Mapping), content
    return {**raw, "message": {**inner, "content": {**content, "parts": [MARKDOWN_PLACEHOLDER]}}}


def write_all_messages(messages: dict[str, Message], messages_dir: Path) -> None:
    """Write all messages to messages/."""
    messages_dir.mkdir(parents=True, exist_ok=True)
    for msg in messages.values():
        msg.write(messages_dir)


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <chatgpt-export.json>", file=sys.stderr)
        sys.exit(1)

    src = Path(sys.argv[1])
    data = load_conversation(src)

    mapping = data["mapping"]
    assert isinstance(mapping, Mapping), type(mapping)
    tree = build_tree(mapping)
    roots = find_roots(mapping)
    assert len(roots) == 1, f"Expected 1 root, got {len(roots)}: {roots}"

    base_dir = src.with_suffix(".splat")
    messages_dir = base_dir / "messages"
    conversations_dir = base_dir / "conversations"

    # Clean up previous run (script owns .splat directory entirely)
    if base_dir.exists():
        shutil.rmtree(base_dir)

    min_ts = compute_min_timestamp(mapping)
    messages = parse_messages(mapping, min_ts)

    # Write all messages
    write_all_messages(messages, messages_dir)

    # Write conversation tree
    conversations_dir.mkdir(parents=True, exist_ok=True)
    for link in enumerate_conversation_links(roots[0], tree, messages, 0, ()):
        link.write(conversations_dir, messages_dir)

    print(f"Wrote {len(messages)} messages to {base_dir}")


if __name__ == "__main__":
    main()
