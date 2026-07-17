#!/usr/bin/env python3
"""Render a chatgpt conversation to readable markdown on stdout.

The fork-fact notation -- what the output guarantees a reader, including
excerpt readers -- is specified and implemented in `chatfs_render`; this
module contributes only the chatgpt-shaped parts: message-file stems
(4-part, with content_type), the `mapping`/`current_node` tree encoding,
and the repair of chatgpt's legitimately turn-less nodes (system
placeholders, empty thought summaries) via `normalize_turnless` -- a
turn-less fork gets a synthetic heading linking its `.json` record, so
fork facts always have an anchor.

Usage:
    chatfs_chatgpt_conversation_render.py <path-to-chat-dir-or-inside>

stdout: rendered markdown.
"""

import sys
from collections.abc import Mapping
from pathlib import Path
from typing import NamedTuple

import chatfs_json
from chatfs_chatgpt_layout import data_dir_of, resolve_chat_dir
from chatfs_chatgpt_types import Conversation, is_conversation
from chatfs_render import ConversationTree, Turn, normalize_turnless, render_tree

VIRTUAL_ROOT = ""
"""Stands in for chatgpt's `parent: null`: the virtual root must be an id
that is named as a parent but is never a node."""


class Stem(NamedTuple):
    """A parsed message-file basename: <iso-ts>.<role>.<uuid>.<content_type>."""

    stem: str
    ts: str
    role: str
    content_type: str

    def note(self) -> str:
        """The heading qualifier: the content type, except `text` (the norm)."""
        return "" if self.content_type == "text" else self.content_type.replace("_", " ")


def load_stems(messages_dir: Path) -> dict[str, Stem]:
    """uuid → its parsed stem, for every splatted message record."""
    stems: dict[str, Stem] = {}
    for entry in messages_dir.iterdir():
        if entry.suffix != ".json":
            continue
        parts = entry.stem.split(".")  # iso-ts has no '.'
        if len(parts) == 4:
            ts, role, uuid, content_type = parts
            stems[uuid] = Stem(entry.stem, ts, role, content_type)
    return stems


def load_turns(messages_dir: Path, stems: dict[str, Stem]) -> dict[str, Turn]:
    """uuid → its Turn, for every message that rendered to a body. Headings
    show date-to-the-minute wall-clock time (matching the claude renderer);
    the full timestamp survives in the link."""
    turns: dict[str, Turn] = {}
    for uuid, s in stems.items():
        md_path = messages_dir / f"{s.stem}.md"
        if md_path.exists():
            turns[uuid] = Turn(
                s.role,
                s.ts[:16],
                f"messages/{s.stem}.md",
                md_path.read_text().rstrip(),
                s.note(),
            )
    return turns


def build_tree(conversation: Conversation) -> ConversationTree:
    """Reshape `mapping` into the shared tree, cross-checking that its
    parent pointers and children arrays agree."""
    mapping = conversation["mapping"]
    children: dict[str, list[str]] = {VIRTUAL_ROOT: []}
    created: dict[str, float] = {}
    for nid, node in mapping.items():
        kids = list(node.get("children") or [])
        for c in kids:
            assert mapping[c].get("parent") == nid, (c, nid)
        children[nid] = kids
        if node.get("parent") is None:
            children[VIRTUAL_ROOT].append(nid)
        message = node.get("message")
        created[nid] = (message.get("create_time") or 0.0) if message else 0.0
    return ConversationTree(
        root=VIRTUAL_ROOT,
        parent_of={nid: node.get("parent") or VIRTUAL_ROOT for nid, node in mapping.items()},
        children=children,
        created=created,
        current=conversation["current_node"],
    )


def make_turn(nid: str, stems: Mapping[str, Stem]) -> Turn:
    """A turn-less fork's anchor: heading only, linking the .json record."""
    s = stems[nid]
    return Turn(s.role, s.ts[:16], f"messages/{s.stem}.json", "", s.note())


def render_conversation(
    conversation: Conversation,
    stems: Mapping[str, Stem],
    turns: Mapping[str, Turn],
) -> tuple[str, int]:
    """The pure render pipeline: conversation mapping + stems + loaded turns →
    the full markdown document. Returns (markdown, turn count)."""
    tree, turns = normalize_turnless(
        build_tree(conversation), turns, lambda nid: make_turn(nid, stems)
    )
    return render_tree(tree, turns)


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path-to-chat-dir-or-inside>", file=sys.stderr)
        sys.exit(2)

    chat_dir = resolve_chat_dir(sys.argv[1])
    parsed = chatfs_json.loads(
        (data_dir_of(chat_dir) / "conversation.json").read_text()
    )
    assert is_conversation(parsed), parsed
    conversation: Conversation = parsed
    messages_dir = chat_dir / "messages"

    stems = load_stems(messages_dir)
    # Every mapping node must have survived the messages_dir round trip -- a
    # missing entry would mean the stem-parsing above silently dropped a
    # message (e.g. a future field containing '.'), which would then vanish
    # from the tree instead of tripping a real splat/render bug. (Unlike
    # claude's tree, most chatgpt nodes are legitimately bodiless -- system
    # placeholders, empty thought summaries -- so this checks .json coverage,
    # not .md coverage; `extract_text_content` raising on an unknown
    # content_type is what guards the .md side, at splat time.)
    assert set(stems) == set(conversation["mapping"]), (
        set(conversation["mapping"]) ^ set(stems)
    )

    turns = load_turns(messages_dir, stems)
    markdown, count = render_conversation(conversation, stems, turns)
    _ = sys.stdout.write(markdown)

    print(f"Rendered {count} turn(s).", file=sys.stderr)


if __name__ == "__main__":
    main()
