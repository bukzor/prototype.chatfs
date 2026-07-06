#!/usr/bin/env python3
"""Render a conversation's mapping to markdown on stdout.

Walks `mapping` from root, emitting one section per textual turn. The
live path (root → current_node) renders unprefixed; dead branches off
each fork are blockquoted at depth = how many forks deep they sit
inside, and appear right after the fork point so they read as
quoted-asides between the parent turn and the live continuation.

Each section: a `# [seq · role · time](messages/<stem>.md)` H1 backref
to the atomic turn-file under the chat dir.

Usage:
    chatfs_chatgpt_conversation_render.py <path-to-chat-dir-or-inside>

stdout: rendered markdown.
"""
import sys
from collections.abc import Mapping

import chatfs_json
from chatfs_chatgpt_layout import DATA_DIR_NAME, resolve_chat_dir
from chatfs_chatgpt_types import Conversation, Node, is_conversation


def live_ancestors(mapping: Mapping[str, Node], current: str) -> set[str]:
    """The live set: `current` and every ancestor up to the root."""
    live: set[str] = set()
    node: str | None = current
    while node is not None:
        live.add(node)
        node = mapping[node].get("parent")
    return live


def primary_child(
    children: list[str],
    live_set: set[str],
    mapping: Mapping[str, Node],
) -> str | None:
    """Pick the child to continue inline. Live child wins; else latest."""
    for c in children:
        if c in live_set:
            return c
    if not children:
        return None

    def ct(c: str) -> float:
        message = mapping[c].get("message")
        if message is None:
            return 0.0
        return message.get("create_time") or 0.0

    return max(children, key=ct)


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path-to-chat-dir-or-inside>", file=sys.stderr)
        sys.exit(2)

    chat_dir = resolve_chat_dir(sys.argv[1])
    parsed = chatfs_json.loads((chat_dir / DATA_DIR_NAME / "conversation.json").read_text())
    assert is_conversation(parsed), parsed
    conversation: Conversation = parsed
    messages_dir = chat_dir / "messages"

    mapping = conversation["mapping"]
    current = conversation["current_node"]

    # uuid → (stem, ts, role, content_type)
    by_uuid: dict[str, tuple[str, str, str, str]] = {}
    for entry in messages_dir.iterdir():
        if entry.suffix != ".json":
            continue
        # stem: <iso-ts>.<role>.<uuid>.<content_type>; iso-ts has no '.'
        stem = entry.stem
        parts = stem.split(".")
        if len(parts) == 4:
            ts, role, uuid, content_type = parts
            by_uuid[uuid] = (stem, ts, role, content_type)

    # Every mapping node must have survived the messages_dir round trip — a
    # missing entry would mean the stem-parsing above silently dropped a
    # message (e.g. a future field containing '.'), which would then vanish
    # from the tree instead of tripping a real splat/render bug. (Unlike
    # claude's tree, most chatgpt nodes are legitimately bodiless — system
    # placeholders, empty thought summaries — so this checks .json coverage,
    # not .md coverage; `extract_text_content` raising on an unknown
    # content_type is what guards the .md side, at splat time.)
    assert set(by_uuid) == set(mapping), set(mapping) ^ set(by_uuid)

    live_set = live_ancestors(mapping, current)

    seq = 0
    prev_depth = -1

    def emit(node_id: str, depth: int) -> None:
        nonlocal seq, prev_depth
        record = by_uuid.get(node_id)
        if record is not None:
            stem, ts, role, content_type = record
            md_path = messages_dir / f"{stem}.md"
            if md_path.exists():
                time_of_day = ts[11:19]  # 'HH:MM:SS' from '<date>T<HH:MM:SS>,<ns><tz>'
                heading_text = f"{seq:03d} · {role} · {time_of_day}"
                if content_type != "text":
                    heading_text += f" ({content_type.replace('_', ' ')})"
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
                        # Same dead branch continuing -- separator must stay quoted.
                        _ = sys.stdout.write(("> " * depth).rstrip() + "\n")
                    else:
                        _ = sys.stdout.write("\n")
                _ = sys.stdout.write(section)
                seq += 1
                prev_depth = depth

        children = list(mapping[node_id].get("children") or [])
        primary = primary_child(children, live_set, mapping)
        for c in children:
            if c == primary:
                continue
            emit(c, depth + 1)
        if primary is not None:
            emit(primary, depth)

    root = next(nid for nid, m in mapping.items() if m.get("parent") is None)
    emit(root, 0)

    print(f"Rendered {seq} turn(s).", file=sys.stderr)


if __name__ == "__main__":
    main()
