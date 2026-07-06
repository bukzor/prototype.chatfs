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
from chatfs_claude_types import ChatMessage, Several, is_conversation


@dataclass
class Turn:
    """A renderable turn: its heading fields plus body. Keyed by uuid in the
    `turns` map, whose keyset is exactly the set of emittable turns."""

    sender: str
    time: str
    link: str
    body: str


def build_children(chat_messages: Several[ChatMessage]) -> dict[str, list[str]]:
    children: dict[str, list[str]] = {}
    for m in chat_messages:
        children.setdefault(m["parent_message_uuid"], []).append(m["uuid"])
    return children


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


def live_ancestors(by_uuid: Mapping[str, ChatMessage], current: str) -> set[str]:
    """The live set: `current` and every ancestor up to the root."""
    live: set[str] = set()
    node = current
    while node in by_uuid:
        live.add(node)
        node = by_uuid[node]["parent_message_uuid"]
    return live


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
            assert node == root, (
                f"turn-less node {node!r} is not the root — every non-root "
                "message must have a rendered turn (enforced by the "
                "set(turns) == set(by_uuid) assert in main(), which must "
                "run before this walk)"
            )
            child_head, child_starts = branch_head, starts
        primary = primary_of[node]
        for c in children.get(node, []):
            if c != primary:
                walk(c, depth + 1, None, True)
        if primary is not None:
            walk(primary, depth, child_head, child_starts)

    walk(root, 0, None, False)
    return order, numbering


def format_subtitle(item: str) -> str:
    """A metadata line, italic so it can't be mistaken for message prose.
    Bare *italics* rather than <sub>: the primary consumers are LLMs and
    plaintext editors, to which <sub> tags are token cost and visual clutter;
    in-browser smallness would serve only the third-ranked consumer. Same
    reasoning that kept anchors out."""
    return f"*{item}*" if item else ""


@dataclass(frozen=True)
class Renderer:
    """Formats fork facts and assembles the markdown. Holds the conversation's
    structure maps so each formatter takes just a `node`, rather than threading
    `numbering`/`children`/`primary_of`/`parent_of` through every signature."""

    numbering: Mapping[str, tuple[int | None, int]]
    children: Mapping[str, list[str]]
    primary_of: Mapping[str, str | None]
    parent_of: Mapping[str, str]
    turns: Mapping[str, Turn]
    live_set: Container[str]

    def number(self, node: str) -> str:
        """`head/seq`, dropping the prefix when the turn is its own branch head —
        so the live branch and every branch head render bare (`034`, not
        `034/034`)."""
        head, seq = self.numbering[node]
        prefix = "" if head in (None, seq) else f"{head:03d}/"
        return f"{prefix}{seq:03d}"

    def parent_is_just_above(self, node: str, prev_seq: int | None) -> bool:
        """Whether this turn's parent is the numbered turn that rendered directly
        above it — i.e. the live continuation, needing no explicit backref."""
        parent = self.parent_of[node]
        return parent in self.numbering and self.numbering[parent][1] == prev_seq

    def backlink(self, node: str, prev_seq: int | None) -> str:
        """` (re: parent)` when the parent is numbered but isn't the turn just
        above (an unnumbered parent — root/origin — has no ref to point at)."""
        parent = self.parent_of[node]
        if parent in self.numbering and not self.parent_is_just_above(node, prev_seq):
            return f" (re: {self.number(parent)})"
        else:
            return ""

    def replies(self, node: str) -> str:
        """Footer item at a fork: all replies in render order, the chosen
        continuation last and explicitly tagged — `←live` when it's on the
        path to `current_leaf_message_uuid`, `←latest` when it's merely the
        most-recently-created child of an already-superseded branch."""
        kids = self.children.get(node, [])
        if len(kids) < 2:
            return ""
        primary = self.primary_of[node]
        assert primary is not None, node
        dead = [self.number(c) for c in kids if c != primary]
        tag = "←live" if primary in self.live_set else "←latest"
        live = f"{self.number(primary)} {tag}"
        return f"replies: {', '.join([*dead, live])}"

    def version_status(self, node: str) -> str:
        """Header item placing this version within its fork — empty when the
        parent isn't a fork. The two cases are converses, and a node is exactly
        one of them: a superseded sibling gets `superseded by: <winner>`, a
        stop-reading-here pointer to the version the conversation continued
        with; the winner gets `prior revisions: <priors>`, the revision chain
        in one canonical place."""
        parent = self.parent_of[node]
        kids = self.children.get(parent, [])
        if len(kids) < 2:
            return ""
        primary = self.primary_of[parent]
        assert primary is not None, node
        if node != primary:
            return f"superseded by: {self.number(primary)}"
        priors = ", ".join(self.number(c) for c in kids if c != primary)
        return f"prior revisions: {priors}"

    def section(self, node: str, depth: int, prev_seq: int | None) -> str:
        """The turn's full markdown block, blockquote-indented to its depth."""
        turn = self.turns[node]
        title = f"# [{self.number(node)} · {turn.sender} · {turn.time}]({turn.link})"
        title += self.backlink(node, prev_seq)
        parts = (
            title,
            format_subtitle(self.version_status(node)),
            turn.body,
            format_subtitle(self.replies(node)),
        )
        body = "\n\n".join(s for s in parts if s) + "\n"
        if depth == 0:
            return body
        prefix = "> " * depth
        return "".join((prefix + line).rstrip() + "\n" for line in body.splitlines())

    def divider(self, node: str, depth: int, prev_depth: int, prev_seq: int | None) -> str:
        """The blank/rule that separates this section from the previous one."""
        if depth == 0 or prev_depth != depth:
            return "\n"
        if self.parent_is_just_above(node, prev_seq):
            return ("> " * depth).rstrip() + "\n"
        # new sibling branch: divide at the *parent's* depth, which closes the
        # previous sibling's blockquote — the two render as separate islands,
        # not one quote with a rule inside — and can't be confused with a body
        # hr at the turns' depth
        outer_blank = ("> " * (depth - 1)).rstrip() + "\n"
        return outer_blank + ("> " * (depth - 1)) + "---\n" + outer_blank

    def render(self, order: list[tuple[str, int]]) -> str:
        out: list[str] = []
        prev_depth = -1
        prev_seq: int | None = None
        for n, (node, depth) in enumerate(order):
            if n > 0:
                out.append(self.divider(node, depth, prev_depth, prev_seq))
            out.append(self.section(node, depth, prev_seq))
            prev_depth = depth
            prev_seq = self.numbering[node][1]
        return "".join(out)


def load_turns(messages_dir: Path) -> dict[str, Turn]:
    """uuid → its Turn, for every message that rendered to a non-empty body.

    The time field keeps the date but truncates to the minute and drops the
    offset — heading noise costs the reader more than sub-minute precision
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
    """Drop messages that splatted to a .json but no .md — a bodiless node such
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

    turns = load_turns(messages_dir)
    chat_messages = prune_bodiless_leaves(tuple(conversation["chat_messages"]), turns)
    by_uuid = {m["uuid"]: m for m in chat_messages}
    parent_of = {m["uuid"]: m["parent_message_uuid"] for m in chat_messages}
    children = build_children(chat_messages)
    root = find_root(chat_messages)
    live_set = live_ancestors(by_uuid, conversation["current_leaf_message_uuid"])
    primary_of = {
        nid: primary_child(children.get(nid, []), live_set, by_uuid)
        for nid in [root, *by_uuid]
    }

    # Every surviving message must have a rendered body on disk — a missing one
    # would silently vanish from numbering, re:-chains, and reply lists. Bodiless
    # cancel leaves are pruned above; anything still missing is a real bug.
    assert set(turns) == set(by_uuid), set(turns) ^ set(by_uuid)

    # When the first message was edited, the root sentinel has several children
    # (the first-message versions). Materialize it as turn 000 ("origin") so the
    # root fork carries a replies subtitle and each version back-points `(re: 000)`.
    # With a single child there is no fork, so origin would be noise — skip it.
    if len(children.get(root, [])) > 1:
        turns[root] = Turn(
            "origin",
            "0000-00-00T00:00",
            f"{DATA_DIR_NAME}/conversation.json",
            "",
        )
        parent_of[root] = ""  # before the beginning: never a uuid, never numbered

    order, numbering = number_turns(root, children, primary_of, turns)
    renderer = Renderer(numbering, children, primary_of, parent_of, turns, live_set)
    _ = sys.stdout.write(renderer.render(order))

    print(f"Rendered {len(order)} turn(s).", file=sys.stderr)


if __name__ == "__main__":
    main()
