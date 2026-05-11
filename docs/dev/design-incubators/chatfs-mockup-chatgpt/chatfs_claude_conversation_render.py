#!/usr/bin/env python3
"""Render a claude conversation to markdown on stdout.

Builds a tree from `chat_messages[*].parent_message_uuid`, walks from
the root downward. The live path (root → `current_leaf_message_uuid`)
renders unprefixed. Dead branches off each fork are blockquoted at
depth = how many forks deep — appearing right after the fork point so
they read as quoted-asides between the parent turn and the live
continuation (mirrors chatgpt-render).

Each section: `# [seq · sender · time](messages/<stem>.md)` H1 backref
to the atomic turn-file under the chat dir.

Usage:
    chatfs_claude_conversation_render.py <path-to-chat-dir-or-inside>

stdout: rendered markdown.
"""
import json
import sys
from collections.abc import Mapping

from chatfs_claude_layout import DATA_DIR_NAME, resolve_chat_dir


def build_children(chat_messages: list[dict]) -> dict[str, list[str]]:
    children: dict[str, list[str]] = {}
    for m in chat_messages:
        children.setdefault(m["parent_message_uuid"], []).append(m["uuid"])
    return children


def find_root(chat_messages: list[dict]) -> str:
    """The root is the message whose parent isn't in our chat_messages set.

    Claude uses an all-zero UUID sentinel as the root-parent.
    """
    uuids = {m["uuid"] for m in chat_messages}
    roots = [m["uuid"] for m in chat_messages if m["parent_message_uuid"] not in uuids]
    assert len(roots) == 1, f"expected 1 root, got {len(roots)}: {roots}"
    return roots[0]


def walk_to_current(by_uuid: Mapping[str, dict], current: str) -> list[str]:
    path: list[str] = []
    node = current
    while node in by_uuid:
        path.append(node)
        node = by_uuid[node]["parent_message_uuid"]
    path.reverse()
    return path


def primary_child(
    candidates: list[str],
    live_set: set[str],
    by_uuid: Mapping[str, dict],
) -> str | None:
    """Pick the child to continue inline. Live child wins; else latest."""
    for c in candidates:
        if c in live_set:
            return c
    if not candidates:
        return None
    return max(candidates, key=lambda c: by_uuid[c]["created_at"])


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path-to-chat-dir-or-inside>", file=sys.stderr)
        sys.exit(2)

    chat_dir = resolve_chat_dir(sys.argv[1])
    conversation = json.loads(
        (chat_dir / DATA_DIR_NAME / "conversation.json").read_text()
    )
    messages_dir = chat_dir / "messages"

    chat_messages = conversation["chat_messages"]
    current = conversation["current_leaf_message_uuid"]
    by_uuid = {m["uuid"]: m for m in chat_messages}
    children = build_children(chat_messages)
    root = find_root(chat_messages)

    # uuid → (stem, ts, sender) — splat writes <iso-ts>.<sender>.<uuid>.{md,json}
    by_uuid_stem: dict[str, tuple[str, str, str]] = {}
    for entry in messages_dir.iterdir():
        if entry.suffix != ".json":
            continue
        stem = entry.stem
        parts = stem.split(".")
        if len(parts) == 3:
            ts, sender, uuid = parts
            by_uuid_stem[uuid] = (stem, ts, sender)

    live_set = set(walk_to_current(by_uuid, current))

    seq = 0
    prev_depth = -1

    def emit(node_id: str, depth: int) -> None:
        nonlocal seq, prev_depth
        record = by_uuid_stem.get(node_id)
        if record is not None:
            stem, ts, sender = record
            md_path = messages_dir / f"{stem}.md"
            if md_path.exists():
                time_of_day = ts[11:19]
                heading_text = f"{seq:03d} · {sender} · {time_of_day}"
                link = f"messages/{stem}.md"
                body = md_path.read_text().rstrip()
                section = f"# [{heading_text}]({link})\n\n{body}\n"
                if depth > 0:
                    prefix = "> " * depth
                    section = "".join(
                        (prefix + line).rstrip() + "\n"
                        for line in section.splitlines()
                    )

                if seq > 0:
                    if depth > 0 and prev_depth == depth:
                        sys.stdout.write(("> " * depth).rstrip() + "\n")
                    else:
                        sys.stdout.write("\n")
                sys.stdout.write(section)
                seq += 1
                prev_depth = depth

        kids = list(children.get(node_id, []))
        primary = primary_child(kids, live_set, by_uuid)
        for c in kids:
            if c == primary:
                continue
            emit(c, depth + 1)
        if primary is not None:
            emit(primary, depth)

    emit(root, 0)

    print(f"Rendered {seq} turn(s).", file=sys.stderr)


if __name__ == "__main__":
    main()
