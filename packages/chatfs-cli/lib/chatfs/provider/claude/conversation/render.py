#!/usr/bin/env python3
"""Render a claude conversation to readable markdown on stdout.

The fork-fact notation -- what the output guarantees a reader, including
excerpt readers -- is specified and implemented in `chatfs.render`; this
module contributes only the claude-shaped parts: message-file stems, the
all-zero root sentinel, and repair of bodiless canceled retries (dropped if
a dead end, spliced out of the tree if the user continued past one).

Usage:
    chatfs-claude-conversation-render <path-to-chat-dir-or-inside>

Reads `conversation.json` via `chat_dir/.data` (the inspection symlink
to `.data/$UUID/`), not by computing that path directly -- path_render
invokes this leaf against a staged scratch sibling whose own name
isn't the bare uuid, so the symlink (already placed by path_render
before this runs, with the correct uuid) is the only path shape valid
in both that context and the final, promoted chat_dir.

stdout: rendered markdown.
"""

from collections.abc import Container, Mapping
from datetime import datetime
from pathlib import Path

import typed_json
from chatfs.layout import DATA_DIR_NAME
from chatfs.provider.claude.conversation.splat import extract_text
from chatfs.provider.claude.types import ChatMessage, Several, is_conversation
from chatfs.render import ConversationTree, Turn, render_tree
from chatfs.shell import sh as chatfs_sh
from chatfs.shell.place import resolve_chat_dir


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


def has_body(msg: ChatMessage, rendered: Container[str]) -> bool:
    """Whether `msg` carries real content -- the same definition `extract_text`
    uses, not the raw presence of a `content` list. A `user_canceled` retry
    still gets a single content block, just one holding an empty `text`;
    checking list-truthiness alone would count that hollow block as a body."""
    return msg["uuid"] in rendered or bool(msg["text"]) or bool(extract_text(tuple(msg["content"])))


def normalize_bodiless_nodes(
    chat_messages: Several[ChatMessage], rendered: Container[str]
) -> Several[ChatMessage]:
    """Repair claude's legitimately turn-less nodes -- a `user_canceled` retry
    that emitted nothing, per `has_body`. A turn-less leaf is dropped --
    nothing to show, no fork to anchor. A turn-less node with exactly one
    child is spliced out, its child reparented to its own parent, so a
    canceled retry the user immediately continued past doesn't fork the tree
    at all. Repairs to a fixpoint, so a chain of these falls leaf-first.

    A turn-less node that still carries real, unrendered content is a
    splat/render bug, not a legitimate gap -- it stays untouched so it trips
    the downstream body-coverage assert in `render_tree`. Likewise a
    turn-less fork (2+ children, none bodied) is left unhandled -- unobserved
    in real data so far, so render_tree's assert catches it rather than this
    function guessing which branch to keep.
    """
    msgs = {m["uuid"]: m for m in chat_messages}
    while True:
        children: dict[str, list[str]] = {}
        for m in msgs.values():
            children.setdefault(m["parent_message_uuid"], []).append(m["uuid"])

        changed = False
        for uuid, m in list(msgs.items()):
            if has_body(m, rendered):
                continue
            kids = children.get(uuid, [])
            if not kids:
                del msgs[uuid]
                changed = True
            elif len(kids) == 1:
                (child,) = kids
                msgs[child] = {**msgs[child], "parent_message_uuid": m["parent_message_uuid"]}
                del msgs[uuid]
                changed = True
        if not changed:
            return tuple(msgs.values())


def render_conversation(
    chat_messages: Several[ChatMessage],
    current: str,
    turns: Mapping[str, Turn],
) -> tuple[str, int]:
    """The pure render pipeline: conversation tree + loaded turns → the full
    markdown document. Returns (markdown, turn count)."""
    chat_messages = normalize_bodiless_nodes(chat_messages, turns)
    return render_tree(build_tree(chat_messages, current), turns)


def render_chat_dir(chat_dir: Path) -> tuple[str, int]:
    """Load conversation.json + messages/ under an already-splatted
    chat_dir and render markdown. Returns (markdown, turn count)."""
    conversation = typed_json.loads(
        (chat_dir / DATA_DIR_NAME / "conversation.json").read_text()
    )
    assert is_conversation(conversation), conversation

    turns = load_turns(chat_dir / "messages")
    return render_conversation(
        tuple(conversation["chat_messages"]),
        conversation["current_leaf_message_uuid"],
        turns,
    )


def main() -> None:
    import sys

    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path-to-chat-dir-or-inside>", file=sys.stderr)
        sys.exit(2)

    chat_dir = resolve_chat_dir(sys.argv[1])
    markdown, count = render_chat_dir(chat_dir)
    _ = sys.stdout.write(markdown)

    chatfs_sh.log(f"Rendered {count} turn(s).")


if __name__ == "__main__":
    main()
