"""Shared conversation-tree rendering, factored out of the provider renderers.

Conversations are trees, not lines: editing or regenerating a message forks
the history. The render keeps every branch but subordinates the dead ones --
the output reads as the live conversation, with abandoned attempts preserved
as quoted asides at their fork points.

Acceptance criteria -- from the headings and fork subtitles alone, a reader can tell:
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
string always finds the definition -- the heading is the anchor.

Providers feed this module a `ConversationTree` (ids, structure, creation
times) plus a `Turn` per node -- the provider-neutral seam. Everything
provider-shaped (wire formats, message-file stems, which nodes are
legitimately turn-less and how to repair that) happens before `render_tree`.
"""

from collections.abc import Callable, Container, Mapping
from dataclasses import dataclass

from chatfs_layout import DATA_DIR_NAME


@dataclass(frozen=True)
class Turn:
    """A renderable turn: its heading fields plus body. Keyed by node id in
    the `turns` map, whose keyset is exactly the set of emittable turns.

    `note` is an optional heading qualifier after the time, e.g. chatgpt's
    non-text content type."""

    sender: str
    time: str
    link: str
    body: str
    note: str = ""


@dataclass(frozen=True)
class ConversationTree:
    """Provider-neutral conversation structure.

    - `root` is virtual: the one id named as a parent that is not itself a
      node; it never has a Turn of its own unless `render_tree` materializes
      an origin for a first-message fork.
    - `children` lists siblings in source order; `created` (epoch seconds)
      breaks dead-fork ordering when the live path doesn't decide.
    - `current` is the live leaf and must be a node of the tree.
    """

    root: str
    parent_of: dict[str, str]
    children: dict[str, list[str]]
    created: dict[str, float]
    current: str


def live_ancestors(tree: ConversationTree) -> set[str]:
    """The live set: `current` and every ancestor up to the root.

    `current` must be a node of the tree -- an unknown leaf (e.g. one pruned
    as bodiless) would yield an empty live set and silently demote every fork
    to latest-wins."""
    assert tree.current in tree.parent_of, tree.current
    live: set[str] = set()
    node = tree.current
    while node in tree.parent_of:
        live.add(node)
        node = tree.parent_of[node]
    return live


def primary_child(
    candidates: list[str],
    live_set: Container[str],
    created: Mapping[str, float],
) -> str | None:
    """Pick the child to continue inline. Live child wins; else latest,
    with a creation-time tie falling to the last-listed sibling."""
    live = next((c for c in candidates if c in live_set), None)
    if live is not None:
        return live
    elif not candidates:
        return None
    else:
        return max(reversed(candidates), key=lambda c: created[c])


def normalize_turnless(
    tree: ConversationTree,
    turns: Mapping[str, Turn],
    make_turn: Callable[[str], Turn],
) -> tuple[ConversationTree, dict[str, Turn]]:
    """Repair a tree whose source legitimately contains turn-less nodes
    (system placeholders, empty thought summaries) into `render_tree`'s
    every-node-has-a-turn invariant:

    - a turn-less leaf is dropped (nothing to show, no fork to anchor);
    - a turn-less pass-through is spliced out, its child taking its place
      in the sibling order;
    - a turn-less fork -- what remains after the above reach fixpoint --
      gets a synthetic Turn from `make_turn`, so the fork's replies and
      back-references have a numbered anchor.
    """
    parent_of = dict(tree.parent_of)
    children = {parent: list(kids) for parent, kids in tree.children.items()}

    changed = True
    while changed:
        changed = False
        for node in [n for n in parent_of if n not in turns]:
            kids = children.get(node, [])
            siblings = children[parent_of[node]]
            if not kids:
                siblings.remove(node)
            elif len(kids) == 1:
                child = kids[0]
                siblings[siblings.index(node)] = child
                parent_of[child] = parent_of[node]
            else:
                continue
            _ = children.pop(node, None)
            del parent_of[node]
            changed = True

    turns = dict(turns)
    for node in parent_of:
        if node not in turns:
            turns[node] = make_turn(node)
    tree = ConversationTree(tree.root, parent_of, children, tree.created, tree.current)
    return tree, turns


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
                f"turn-less node {node!r} is not the root -- every non-root "
                "node must have a rendered turn (enforced by the coverage "
                "assert in render_tree; providers with legitimately turn-less "
                "nodes repair theirs via normalize_turnless first)"
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
        """`head/seq`, dropping the prefix when the turn is its own branch head --
        so the live branch and every branch head render bare (`034`, not
        `034/034`)."""
        head, seq = self.numbering[node]
        prefix = "" if head in (None, seq) else f"{head:03d}/"
        return f"{prefix}{seq:03d}"

    def parent_is_just_above(self, node: str, prev_seq: int | None) -> bool:
        """Whether this turn's parent is the numbered turn that rendered directly
        above it -- i.e. the live continuation, needing no explicit backref."""
        parent = self.parent_of[node]
        return parent in self.numbering and self.numbering[parent][1] == prev_seq

    def backlink(self, node: str, prev_seq: int | None) -> str:
        """` (re: parent)` when the parent is numbered but isn't the turn just
        above (an unnumbered parent -- root/origin -- has no ref to point at)."""
        parent = self.parent_of[node]
        if parent in self.numbering and not self.parent_is_just_above(node, prev_seq):
            return f" (re: {self.number(parent)})"
        else:
            return ""

    def replies(self, node: str) -> str:
        """Footer item at a fork: all replies in render order, the chosen
        continuation last and explicitly tagged -- `←live` when it's on the
        path to the current leaf, `←latest` when it's merely the
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
        """Header item placing this version within its fork -- empty when the
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
        note = f" ({turn.note})" if turn.note else ""
        title = f"# [{self.number(node)} · {turn.sender} · {turn.time}{note}]({turn.link})"
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
        """The separator above this section. A later sibling attempt gets a
        rule at the fork's depth, closing the previous attempt's island; every
        other boundary is a blank quoted at the shallower of the two depths,
        which keeps a branch and its nested asides one contiguous blockquote
        island (and at trunk depth degenerates to a plain blank line)."""
        head, seq = self.numbering[node]
        if head == seq and not self.parent_is_just_above(node, prev_seq):
            # the rule sits one level shallower than the sibling attempts, so
            # it can't be confused with a body hr at the turns' depth
            quote = "> " * (depth - 1)
            blank = quote.rstrip() + "\n"
            return blank + quote + "---\n" + blank
        else:
            return ("> " * min(depth, prev_depth)).rstrip() + "\n"

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


def render_tree(tree: ConversationTree, turns: Mapping[str, Turn]) -> tuple[str, int]:
    """The provider-neutral render pipeline: normalized tree + turns → the
    full markdown document. Returns (markdown, turn count)."""
    # Every node must have a rendered turn -- a missing one would silently
    # vanish from numbering, re:-chains, and reply lists; an extra one is a
    # turn the tree lost track of. Providers repair legitimate gaps before
    # this point (claude: prune_bodiless_leaves; chatgpt: normalize_turnless).
    assert set(turns) == set(tree.parent_of), set(turns) ^ set(tree.parent_of)

    turns = dict(turns)
    parent_of = dict(tree.parent_of)
    live_set = live_ancestors(tree)
    primary_of = {
        nid: primary_child(tree.children.get(nid, []), live_set, tree.created)
        for nid in [tree.root, *parent_of]
    }

    # When the first message was edited, the virtual root has several children
    # (the first-message versions). Materialize it as turn 000 ("origin") so the
    # root fork carries a replies subtitle and each version back-points `(re: 000)`.
    # With a single child there is no fork, so origin would be noise -- skip it.
    if len(tree.children.get(tree.root, [])) > 1:
        turns[tree.root] = Turn(
            "origin",
            "0000-00-00T00:00",
            f"{DATA_DIR_NAME}/conversation.json",
            "",
        )
        parent_of[tree.root] = ""  # before the beginning: never an id, never numbered

    order, numbering = number_turns(tree.root, tree.children, primary_of, turns)
    renderer = Renderer(numbering, tree.children, primary_of, parent_of, turns, live_set)
    return renderer.render(order), len(order)
