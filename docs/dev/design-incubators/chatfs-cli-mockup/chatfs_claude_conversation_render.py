#!/usr/bin/env python3
"""Render a claude conversation to readable markdown on stdout.

The fork-fact notation -- what the output guarantees a reader, including
excerpt readers -- is specified and implemented in `chatfs_render`; this
module contributes only the claude-shaped parts: message-file stems, the
all-zero root sentinel, and pruning of bodiless canceled retries.

Usage:
    chatfs_claude_conversation_render.py <path-to-chat-dir-or-inside>

Reads `conversation.json` via `chat_dir/.data` (the inspection symlink
to `.data/$UUID/`), not by computing that path directly -- path_render
invokes this leaf against a staged scratch sibling whose own name
isn't the bare uuid, so the symlink (already placed by path_render
before this runs, with the correct uuid) is the only path shape valid
in both that context and the final, promoted chat_dir.

stdout: rendered markdown.
"""

import sys
from collections.abc import Container, Mapping
from datetime import datetime
from pathlib import Path

import chatfs_json
from chatfs_claude_layout import DATA_DIR_NAME, resolve_chat_dir
from chatfs_claude_types import ChatMessage, Several, is_conversation
from chatfs_render import ConversationTree, Turn, render_tree


def find_root(chat_messages: Several[ChatMessage]) -> str:
    """Return the virtual root: the all-zero UUID sentinel that every
    top-level message names as parent.

    Editing the first message re-parents each version to the same sentinel,
    so a conversation can have several top-level siblings but always exactly
    one sentinel.
    """
    uuids = {m["uuid"] for m in chat_messages}
    root_parents = {
        m["parent_message_uuid"]
        for m in chat_messages
        if m["parent_message_uuid"] not in uuids
    }
    assert len(root_parents) == 1, f"expected 1 root-parent, got: {root_parents}"
    return root_parents.pop()


def build_tree(chat_messages: Several[ChatMessage], current: str) -> ConversationTree:
    root = find_root(chat_messages)
    children: dict[str, list[str]] = {root: []}
    for m in chat_messages:
        children.setdefault(m["parent_message_uuid"], []).append(m["uuid"])
    return ConversationTree(
        root=root,
        parent_of={m["uuid"]: m["parent_message_uuid"] for m in chat_messages},
        children=children,
        created={
            m["uuid"]: datetime.fromisoformat(m["created_at"]).timestamp()
            for m in chat_messages
        },
        current=current,
    )


def load_turns(messages_dir: Path) -> dict[str, Turn]:
    """uuid → its Turn, for every message that rendered to a non-empty body.

    The time field keeps the date but truncates to the minute and drops the
    offset -- heading noise costs the reader more than sub-minute precision
    buys, and per-message wall-clock local time is what a human wants to
    read. The full timestamp, offset included, survives in the link; the
    only ambiguity the truncation admits is the annual DST fall-back fold,
    which the link resolves."""
    turns: dict[str, Turn] = {}
    for entry in messages_dir.iterdir():
        if entry.suffix != ".json":
            continue
        parts = entry.stem.split(".")
        if len(parts) != 3:
            continue
        ts, sender, uuid = parts
        md_path = messages_dir / f"{entry.stem}.md"
        if not md_path.exists():
            continue
        turns[uuid] = Turn(
            sender, ts[:16], f"messages/{entry.stem}.md", md_path.read_text().rstrip()
        )
    return turns


def prune_bodiless_leaves(
    chat_messages: Several[ChatMessage], rendered: Container[str]
) -> Several[ChatMessage]:
    """Drop messages that splatted to a .json but no .md -- a bodiless node such
    as a `user_canceled` retry that emitted nothing. Keeping one would fabricate
    a fork whose sibling has no turn to number. Prunes to a fixpoint, so a chain
    of bodiless nodes falls leaf-first; a bodiless node that still carries
    content or a surviving child is a splat/render bug, so it stays and trips
    the downstream body-coverage check."""
    msgs = tuple(chat_messages)
    while True:
        parents = {m["parent_message_uuid"] for m in msgs}
        kept = tuple(
            m
            for m in msgs
            if m["uuid"] in rendered
            or m["text"]
            or m["content"]
            or m["uuid"] in parents
        )
        if len(kept) == len(msgs):
            return kept
        msgs = kept


def render_conversation(
    chat_messages: Several[ChatMessage],
    current: str,
    turns: Mapping[str, Turn],
) -> tuple[str, int]:
    """The pure render pipeline: conversation tree + loaded turns → the full
    markdown document. Returns (markdown, turn count)."""
    chat_messages = prune_bodiless_leaves(chat_messages, turns)
    return render_tree(build_tree(chat_messages, current), turns)


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path-to-chat-dir-or-inside>", file=sys.stderr)
        sys.exit(2)

    chat_dir = resolve_chat_dir(sys.argv[1])
    conversation = chatfs_json.loads(
        (chat_dir / DATA_DIR_NAME / "conversation.json").read_text()
    )
    assert is_conversation(conversation), conversation

    turns = load_turns(chat_dir / "messages")
    markdown, count = render_conversation(
        tuple(conversation["chat_messages"]),
        conversation["current_leaf_message_uuid"],
        turns,
    )
    _ = sys.stdout.write(markdown)

    print(f"Rendered {count} turn(s).", file=sys.stderr)


if __name__ == "__main__":
    main()
