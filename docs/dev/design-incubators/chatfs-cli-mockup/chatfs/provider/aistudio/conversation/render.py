#!/usr/bin/env python3
"""Render an AI Studio conversation to readable markdown on stdout.

The fork-fact notation -- what the output guarantees a reader -- is
specified and implemented in `chatfs_render`; this module contributes
only the aistudio-shaped parts: message-file stems (index-led, no
native id) and the tree AI Studio's wire shape actually has, which is
none -- `chunkedPrompt.chunks` is a flat, chronologically-ordered list
with no parent/child linkage at all (see
dev.kb/claims.kb/aistudio-jspb-prompt-shape.md, "Turn order is linear").
`build_tree` therefore produces a straight predecessor chain, never a
real fork; `current` is always the chain's last turn.

Usage:
    chatfs_aistudio_conversation_render.py <path-to-chat-dir-or-inside>

stdout: rendered markdown.
"""

import sys
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

import chatfs_json
from chatfs_aistudio_layout import resolve_chat_dir
from chatfs_aistudio_types import Turn as RawTurn
from chatfs_aistudio_types import is_turn
from chatfs_render import ConversationTree, Turn, render_tree

VIRTUAL_ROOT = ""
"""Stands in for "before the first turn": the virtual root must be an id
that is named as a parent but is never a node."""


def parse_stem(stem: str) -> tuple[int, str, str]:
    """`{index}.{role}[.thought]` -> (index, role, note)."""
    parts = stem.split(".")
    assert len(parts) in (2, 3), stem
    note = parts[2] if len(parts) == 3 else ""
    assert note in ("", "thought"), stem
    return int(parts[0]), parts[1], note


def _time(raw: RawTurn) -> str:
    """Local wall-clock time truncated to the minute, matching the other
    two providers' headings -- the full offset survives in the link."""
    seconds = int(raw["createTime"][0])
    dt = datetime.fromtimestamp(seconds, tz=timezone.utc).astimezone()
    return f"{dt:%Y-%m-%dT%H:%M}"


def load_turns(messages_dir: Path) -> tuple[dict[str, Turn], dict[str, float]]:
    """stem -> its Turn, and stem -> its epoch seconds, for every splatted
    turn that rendered a body. `created` is carried through even though a
    fork-less chain never consults it (see `chatfs_render.primary_child`)
    -- it's the real value, not a fabricated one, so a genuine future fork
    would tie-break correctly rather than silently by insertion order."""
    turns: dict[str, Turn] = {}
    created: dict[str, float] = {}
    for entry in messages_dir.glob("*.json"):
        md_path = entry.with_suffix(".md")
        if not md_path.exists():
            continue
        _, role, note = parse_stem(entry.stem)
        raw = chatfs_json.loads(entry.read_text())
        assert is_turn(raw), raw
        turns[entry.stem] = Turn(
            role, _time(raw), f"messages/{entry.stem}.md", md_path.read_text().rstrip(), note
        )
        created[entry.stem] = int(raw["createTime"][0])
    return turns, created


def build_tree(ids: list[str], created: Mapping[str, float]) -> ConversationTree:
    parent_of: dict[str, str] = {}
    children: dict[str, list[str]] = {VIRTUAL_ROOT: []}
    prev = VIRTUAL_ROOT
    for id_ in ids:
        parent_of[id_] = prev
        children.setdefault(prev, []).append(id_)
        children[id_] = []
        prev = id_
    return ConversationTree(VIRTUAL_ROOT, parent_of, children, dict(created), ids[-1])


def render_conversation(
    turns: Mapping[str, Turn], created: Mapping[str, float]
) -> tuple[str, int]:
    """The pure render pipeline: loaded turns, ordered by their index-led
    stem, -> the full markdown document. Returns (markdown, turn count)."""
    ids = sorted(turns, key=lambda stem: int(stem.split(".")[0]))
    return render_tree(build_tree(ids, created), turns)


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path-to-chat-dir-or-inside>", file=sys.stderr)
        sys.exit(2)

    chat_dir = resolve_chat_dir(sys.argv[1])
    turns, created = load_turns(chat_dir / "messages")
    markdown, count = render_conversation(turns, created)
    _ = sys.stdout.write(markdown)

    print(f"Rendered {count} turn(s).", file=sys.stderr)


if __name__ == "__main__":
    main()
