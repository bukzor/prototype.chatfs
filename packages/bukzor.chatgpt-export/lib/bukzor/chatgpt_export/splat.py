#!/usr/bin/env python3
"""Splat a ChatGPT export JSON into messages/ and conversations/ directories."""

import copy
import json
import os
import shutil
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path

MARKDOWN_PLACEHOLDER = "$MARKDOWN"


@dataclass
class Conversation:
    """A linear path through the message tree."""

    id: str  # node_id where this conversation diverged (or root if linear)
    path: list[str]  # node_ids from root to leaf


def load_conversation(path: Path) -> dict:
    with path.open() as f:
        return json.load(f)


def format_timestamp(unix_ts: float | Decimal | str) -> str:
    """Format timestamp as ISO 8601 with nanoseconds, like `date -Ins`."""
    unix_ts = Decimal(unix_ts)
    dt = datetime.fromtimestamp(int(unix_ts)).astimezone()
    fractional = f"{unix_ts % 1:.9f}"[2:]  # nanoseconds
    return dt.strftime(f"%Y-%m-%dT%H:%M:%S,{fractional}%z")


def build_tree(mapping: dict) -> dict[str, list[str]]:
    """Return {parent_id: [child_ids]} for tree traversal."""
    tree: dict[str, list[str]] = {}
    for node_id, node in mapping.items():
        parent = node.get("parent")
        if parent is not None:
            tree.setdefault(parent, []).append(node_id)
    return tree


def get_node_timestamp(node: dict, default: float = 0.0) -> float:
    """Extract create_time from node's message, or default if absent."""
    msg = node.get("message")
    if msg is None:
        return default
    return msg.get("create_time") or default


def compute_min_timestamp(mapping: dict) -> float:
    """Find the earliest non-null timestamp across all nodes."""
    timestamps = [
        msg.get("create_time")
        for node in mapping.values()
        if (msg := node.get("message")) and msg.get("create_time")
    ]
    return min(timestamps) if timestamps else 0.0


def get_node_role(node: dict) -> str:
    """Extract role from node's message, or 'root' if no message."""
    msg = node.get("message")
    if msg is None:
        return "root"
    author = msg.get("author")
    if author is None:
        return "unknown"
    return author.get("role", "unknown")


def extract_text_content(node: dict) -> str | None:
    """Extract text content from node's message, if present."""
    msg = node.get("message")
    if msg is None:
        return None
    content = msg.get("content")
    if content is None:
        return None
    if content.get("content_type") != "text":
        return None
    parts = content.get("parts", [])
    if not parts:
        return None
    return "\n".join(str(p) for p in parts if p)


def node_filename(node_id: str, timestamp: float, role: str) -> str:
    """Generate filename with ISO timestamp and role."""
    ts_str = format_timestamp(timestamp)
    return f"{ts_str}.{role}.{node_id}"


def write_message(node: dict, dest: Path, text_content: str | None) -> None:
    """Write node JSON and optional markdown file to messages/."""
    dest.parent.mkdir(parents=True, exist_ok=True)

    if text_content:
        md_path = dest.with_suffix(".md")
        md_path.write_text(text_content)
        node = copy.deepcopy(node)
        node["message"]["content"]["parts"] = [MARKDOWN_PLACEHOLDER]

    with dest.open("w") as f:
        json.dump(node, f, indent=2)


def find_roots(mapping: dict) -> list[str]:
    """Find nodes with no parent (roots of the tree)."""
    return [
        node_id
        for node_id, node in mapping.items()
        if node.get("parent") is None
    ]


def enumerate_conversations(
    mapping: dict,
    tree: dict[str, list[str]],
    node_id: str,
    conv_id: str,
    path: list[str],
    min_ts: float,
) -> Iterator[Conversation]:
    """Walk tree from root, yielding Conversation for each leaf.

    conv_id is set to root initially. At forks, the earliest child (by timestamp)
    continues with the same conv_id; later children get their own IDs.
    """
    path = path + [node_id]
    children = sorted(
        tree.get(node_id, []),
        key=lambda c: get_node_timestamp(mapping[c], min_ts),
    )

    if not children:
        yield Conversation(id=conv_id, path=path)
        return

    # First child continues the original conversation
    yield from enumerate_conversations(mapping, tree, children[0], conv_id, path, min_ts)
    # Later children are forks, get their own IDs
    for child in children[1:]:
        yield from enumerate_conversations(mapping, tree, child, child, path, min_ts)


def write_all_messages(mapping: dict, messages_dir: Path, min_ts: float) -> dict[str, str]:
    """Write all messages to messages/, return {node_id: basename}."""
    basenames = {}
    for node_id, node in mapping.items():
        timestamp = get_node_timestamp(node, min_ts)
        role = get_node_role(node)
        basename = node_filename(node_id, timestamp, role)
        basenames[node_id] = basename
        text_content = extract_text_content(node)
        write_message(node, messages_dir / f"{basename}.json", text_content)
    return basenames


def write_conversation_symlinks(
    path: list[str],
    basenames: dict[str, str],
    conv_dir: Path,
    messages_dir: Path,
) -> None:
    """Create symlinks in conversation dir pointing to messages/.

    Symlink names are prefixed with zero-padded sequence numbers to ensure
    correct ordering via glob/ls, since ChatGPT timestamps don't preserve
    causality (assistant create_time often precedes user message).
    """
    conv_dir.mkdir(parents=True, exist_ok=True)
    rel_messages = os.path.relpath(messages_dir, conv_dir)

    # Zero-pad to handle conversations up to 999 messages
    width = 3

    for seq, node_id in enumerate(path):
        basename = basenames[node_id]
        seq_prefix = f"{seq:0{width}d}."

        # Symlink .json
        json_link = conv_dir / f"{seq_prefix}{basename}.json"
        json_target = f"{rel_messages}/{basename}.json"
        json_link.symlink_to(json_target)
        # Symlink .md if it exists
        md_src = messages_dir / f"{basename}.md"
        if md_src.exists():
            md_link = conv_dir / f"{seq_prefix}{basename}.md"
            md_link.symlink_to(f"{rel_messages}/{basename}.md")


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <chatgpt-export.json>", file=sys.stderr)
        sys.exit(1)

    src = Path(sys.argv[1])
    data = load_conversation(src)

    mapping = data["mapping"]
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

    # Write all messages
    basenames = write_all_messages(mapping, messages_dir, min_ts)

    # Find all conversations and write symlinks
    conv_count = 0
    for conv in enumerate_conversations(mapping, tree, roots[0], roots[0], [], min_ts):
        conv_name = basenames[conv.id]
        conv_dir = conversations_dir / conv_name
        write_conversation_symlinks(conv.path, basenames, conv_dir, messages_dir)
        conv_count += 1

    print(f"Wrote {len(mapping)} messages, {conv_count} conversations to {base_dir}")


if __name__ == "__main__":
    main()
