#!/usr/bin/env python3
"""Render a claude conversation to readable markdown on stdout.

Conversations are trees, not lines: editing or regenerating a message
forks the history. The render keeps every branch but subordinates the
dead ones — the output reads as the live conversation, with abandoned
attempts preserved as quoted asides at their fork points (mirrors
chatgpt-render).

Acceptance criteria — from the headings and fork subtitles alone, a reader can tell:
- which turns form the live conversation, and which were abandoned;
- where each fork happened, what the alternatives were, and which one
  the conversation continued;
- for any turn, how to reach its parent and its atomic source file.

The audience includes excerpt readers (grep windows, partial reads), so fork
facts repeat across positions: the fork parent lists all replies, each
superseded version names the winner, and the winner lists its priors.

Fork facts render as *italic* metadata lines in two zones: version status
(superseded-by, prior-revisions) above the body, forward navigation (replies,
live one marked) below it.

Heading numbers are stable handles for cross-reference, not chronology.
Cross-references repeat the heading's number verbatim, so searching a ref
string always finds the definition — the heading is the anchor.

Usage:
    chatfs_claude_conversation_render.py <path-to-chat-dir-or-inside>

stdout: rendered markdown.
"""

import sys
from collections.abc import Container, Mapping
from dataclasses import dataclass
from pathlib import Path

import chatfs_json
from chatfs_claude_layout import DATA_DIR_NAME, resolve_chat_dir
from chatfs_claude_types import ChatMessage, is_conversation


@dataclass
class Turn:
    """A renderable turn: its heading fields plus body. Keyed by uuid in the
    `turns` map, whose keyset is exactly the set of emittable turns."""

    uuid: str
    sender: str
    time: str
    link: str
    body: str


def build_children(chat_messages: list[ChatMessage]) -> dict[str, list[str]]:
    children: dict[str, list[str]] = {}
    for m in chat_messages:
        children.setdefault(m["parent_message_uuid"], []).append(m["uuid"])
    return children


def find_root(chat_messages: list[ChatMessage]) -> str:
    """Return the virtual root: the shared parent of all top-level messages.

    Claude uses an all-zero UUID sentinel as the root-parent. Editing the
    first message re-parents each version to that sentinel, so a conversation
    can have several sibling roots — all naming the same sentinel as parent.
    We return the sentinel itself. With one first message it stays unrendered
    (`number_turns` finds no turn for it and descends into its child); with
    several, `main` materializes it as turn `000 · origin` so the fork shows.
    """
    uuids = {m["uuid"] for m in chat_messages}
    root_parents = {
        m["parent_message_uuid"]
        for m in chat_messages
        if m["parent_message_uuid"] not in uuids
    }
    assert len(root_parents) == 1, f"expected 1 root-parent, got: {root_parents}"
    return root_parents.pop()


def walk_to_current(by_uuid: Mapping[str, ChatMessage], current: str) -> list[str]:
    path: list[str] = []
    node = current
    while node in by_uuid:
        path.append(node)
        node = by_uuid[node]["parent_message_uuid"]
    path.reverse()
    return path


def primary_child(
    candidates: list[str],
    live_set: Container[str],
    by_uuid: Mapping[str, ChatMessage],
) -> str | None:
    """Pick the child to continue inline. Live child wins; else latest."""
    for c in candidates:
        if c in live_set:
            return c
    if not candidates:
        return None
    return max(candidates, key=lambda c: by_uuid[c]["created_at"])


def number_turns(
    root: str,
    children: Mapping[str, list[str]],
    primary_of: Mapping[str, str | None],
    turns: Container[str],
) -> tuple[list[tuple[str, int]], dict[str, tuple[int | None, int]]]:
    """Assign each turn its emit order, depth, and (branch-head, seq) number.

    Branch head is None on the live trunk; otherwise the seq of the first
    turn of the branch this turn belongs to. Non-primary fork children start
    a new branch (head = their own seq); the primary child continues its
    parent's branch.
    """
    order: list[tuple[str, int]] = []
    numbering: dict[str, tuple[int | None, int]] = {}
    seq = 0

    def walk(node: str, depth: int, branch_head: int | None, starts: bool) -> None:
        nonlocal seq
        if node in turns:
            head = seq if starts else branch_head
            numbering[node] = (head, seq)
            order.append((node, depth))
            child_head, child_starts = head, False
            seq += 1
        else:
            child_head, child_starts = branch_head, starts
        primary = primary_of[node]
        for c in children.get(node, []):
            if c != primary:
                walk(c, depth + 1, None, True)
        if primary is not None:
            walk(primary, depth, child_head, child_starts)

    walk(root, 0, None, False)
    return order, numbering


def format_number(numbering: Mapping[str, tuple[int | None, int]], node: str) -> str:
    """`head/seq`, dropping the prefix when the turn is its own branch head — so
    the live branch and every branch head render bare (`034`, not `034/034`)."""
    head, seq = numbering[node]
    prefix = "" if head in (None, seq) else f"{head:03d}/"
    return f"{prefix}{seq:03d}"


def format_backlink(
    node: str,
    prev_seq: int | None,
    numbering: Mapping[str, tuple[int | None, int]],
    parent_of: Mapping[str, str],
) -> str:
    """` (re: parent)` when the parent isn't the turn just above."""
    parent = parent_of[node]
    if parent in numbering and numbering[parent][1] != prev_seq:
        return f" (re: {format_number(numbering, parent)})"
    return ""


def format_subtitle(*items: str) -> str:
    """One metadata line from the non-empty items: italic, so it can't be
    mistaken for message prose. Bare *italics* rather than <sub>: the primary
    consumers are LLMs and plaintext editors, to which <sub> tags are token
    cost and visual clutter; in-browser smallness would serve only the
    third-ranked consumer. Same reasoning that kept anchors out."""
    joined = " · ".join(i for i in items if i)
    return f"*{joined}*" if joined else ""


def format_replies(
    node: str,
    numbering: Mapping[str, tuple[int | None, int]],
    children: Mapping[str, list[str]],
    primary_of: Mapping[str, str | None],
) -> str:
    """Footer item at a fork: all replies in render order, the live one last
    and marked `←live` (liveness shouldn't rely on the unstated last-is-live
    convention). Sits at the section's end, directly above the descent it
    describes — the superseded replies render below as quoted asides; the live
    one continues the conversation at this turn's depth."""
    kids = children.get(node, [])
    if len(kids) < 2:
        return ""
    primary = primary_of[node]
    assert primary is not None, node
    dead = [format_number(numbering, c) for c in kids if c != primary]
    live = f"{format_number(numbering, primary)} ←live"
    return f"replies: {', '.join([*dead, live])}"


def format_supersession(
    node: str,
    numbering: Mapping[str, tuple[int | None, int]],
    children: Mapping[str, list[str]],
    primary_of: Mapping[str, str | None],
    parent_of: Mapping[str, str],
) -> str:
    """Header item on a superseded fork sibling: names the version the
    conversation continued with — one hop to the winner from any excerpt.
    A stop-reading-here warning, so it precedes the body. The winner's
    converse view is format_priors."""
    parent = parent_of[node]
    kids = children.get(parent, [])
    if len(kids) < 2:
        return ""
    primary = primary_of[parent]
    assert primary is not None, node
    if node == primary:
        return ""
    return f"superseded by: {format_number(numbering, primary)}"


def format_priors(
    node: str,
    numbering: Mapping[str, tuple[int | None, int]],
    children: Mapping[str, list[str]],
    primary_of: Mapping[str, str | None],
    parent_of: Mapping[str, str],
) -> str:
    """Header item on a fork winner: its superseded priors in succession
    order, so the revision chain stays recoverable in one canonical place.
    The winner renders just below its superseded asides, so this line lands
    right after the turns it names, explaining them on the way out."""
    parent = parent_of[node]
    kids = children.get(parent, [])
    if len(kids) < 2:
        return ""
    primary = primary_of[parent]
    assert primary is not None, node
    if node != primary:
        return ""
    priors = ", ".join(format_number(numbering, c) for c in kids if c != primary)
    return f"prior revisions: {priors}"


def render_markdown(
    order: list[tuple[str, int]],
    numbering: Mapping[str, tuple[int | None, int]],
    children: Mapping[str, list[str]],
    primary_of: Mapping[str, str | None],
    parent_of: Mapping[str, str],
    turns: Mapping[str, Turn],
) -> str:
    out: list[str] = []
    prev_depth = -1
    prev_seq: int | None = None
    for n, (node, depth) in enumerate(order):
        turn = turns[node]
        number = format_number(numbering, node)
        title = f"# [{number} · {turn.sender} · {turn.time}]({turn.link})"
        title += format_backlink(node, prev_seq, numbering, parent_of)
        header = format_subtitle(
            format_supersession(node, numbering, children, primary_of, parent_of),
            format_priors(node, numbering, children, primary_of, parent_of),
        )
        footer = format_subtitle(
            format_replies(node, numbering, children, primary_of),
        )
        section = (
            "\n\n".join(s for s in (title, header, turn.body, footer) if s) + "\n"
        )
        if depth > 0:
            prefix = "> " * depth
            section = "".join(
                (prefix + line).rstrip() + "\n" for line in section.splitlines()
            )
        if n > 0:
            if depth > 0 and prev_depth == depth:
                parent = parent_of[node]
                if parent not in numbering or numbering[parent][1] != prev_seq:
                    # new sibling branch: divide at the *parent's* depth, which
                    # closes the previous sibling's blockquote — the two render
                    # as separate islands, not one quote with a rule inside —
                    # and can't be confused with a body hr at the turns' depth
                    outer_blank = ("> " * (depth - 1)).rstrip() + "\n"
                    out.append(outer_blank + ("> " * (depth - 1)) + "---\n" + outer_blank)
                else:
                    out.append(("> " * depth).rstrip() + "\n")
            else:
                out.append("\n")
        out.append(section)
        prev_depth = depth
        prev_seq = numbering[node][1]
    return "".join(out)


def read_message_index(messages_dir: Path) -> dict[str, tuple[str, str, str]]:
    """uuid → (stem, ts, sender), parsed from `<iso-ts>.<sender>.<uuid>.json`."""
    index: dict[str, tuple[str, str, str]] = {}
    for entry in messages_dir.iterdir():
        if entry.suffix != ".json":
            continue
        parts = entry.stem.split(".")
        if len(parts) == 3:
            ts, sender, uuid = parts
            index[uuid] = (entry.stem, ts, sender)
    return index


def load_turns(
    messages_dir: Path, index: Mapping[str, tuple[str, str, str]]
) -> dict[str, Turn]:
    """Read each rendered turn-file. The returned map's keyset is exactly the
    emittable turns (those with a `.md` body on disk)."""
    turns: dict[str, Turn] = {}
    for uuid, (stem, ts, sender) in index.items():
        md_path = messages_dir / f"{stem}.md"
        if not md_path.exists():
            continue
        # ISO date+time, sliced from `2026-05-29T09:21:56,716…`. Conversations
        # span days, so the heading carries the full date.
        when = ts[:19]
        turns[uuid] = Turn(
            uuid, sender, when, f"messages/{stem}.md", md_path.read_text().rstrip()
        )
    return turns


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path-to-chat-dir-or-inside>", file=sys.stderr)
        sys.exit(2)

    chat_dir = resolve_chat_dir(sys.argv[1])
    conversation = chatfs_json.loads(
        (chat_dir / DATA_DIR_NAME / "conversation.json").read_text()
    )
    assert is_conversation(conversation), conversation
    messages_dir = chat_dir / "messages"

    chat_messages = conversation["chat_messages"]
    by_uuid = {m["uuid"]: m for m in chat_messages}
    parent_of = {m["uuid"]: m["parent_message_uuid"] for m in chat_messages}
    children = build_children(chat_messages)
    root = find_root(chat_messages)
    live_set = set(walk_to_current(by_uuid, conversation["current_leaf_message_uuid"]))
    primary_of = {
        nid: primary_child(children.get(nid, []), live_set, by_uuid)
        for nid in [root, *by_uuid]
    }

    index = read_message_index(messages_dir)
    turns = load_turns(messages_dir, index)
    # Every conversation message must have a rendered body on disk — a missing
    # one would silently vanish from numbering, re:-chains, and reply lists.
    assert set(turns) == set(by_uuid), set(turns) ^ set(by_uuid)

    # When the first message was edited, the root sentinel has several children
    # (the first-message versions). Materialize it as turn 000 ("origin") so the
    # root fork carries a replies subtitle and each version back-points `(re: 000)`.
    # With a single child there is no fork, so origin would be noise — skip it.
    if len(children.get(root, [])) > 1:
        turns[root] = Turn(
            root,
            "origin",
            "0000-00-00T00:00:00",
            f"{DATA_DIR_NAME}/conversation.json",
            "",
        )
        parent_of[root] = ""  # before the beginning: never a uuid, never numbered

    order, numbering = number_turns(root, children, primary_of, turns)
    _ = sys.stdout.write(
        render_markdown(order, numbering, children, primary_of, parent_of, turns)
    )

    print(f"Rendered {len(order)} turn(s).", file=sys.stderr)


if __name__ == "__main__":
    main()
