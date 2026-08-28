"""Tests for the shared turn-less tree repair; the render pipeline itself is
pinned end-to-end by the claude renderer's golden test."""

from chatfs.render import ConversationTree, Turn, normalize_turnless, render_tree


def turn(nid: str) -> Turn:
    return Turn("human", "T", "L", f"body {nid}")


def make_tree(
    parent_of: dict[str, str], current: str, uncaptured: set[str] | None = None
) -> ConversationTree:
    """Sibling order is `parent_of` insertion order; the root is ""."""
    children: dict[str, list[str]] = {"": []}
    for nid, parent in parent_of.items():
        _ = children.setdefault(nid, [])
        children.setdefault(parent, []).append(nid)
    return ConversationTree(
        root="",
        parent_of=dict(parent_of),
        children=children,
        created=dict.fromkeys(parent_of, 0.0),
        current=current,
        uncaptured_versions=uncaptured or frozenset[str](),
    )


class DescribeNormalizeTurnless:
    def it_drops_a_turnless_leaf_chain(self):
        # a dead branch of nothing-to-show nodes falls leaf-first, in full
        tree = make_tree({"a": "", "s1": "a", "s2": "s1"}, current="a")
        turns = {"a": turn("a")}
        tree, turns = normalize_turnless(tree, turns, turn)
        assert set(tree.parent_of) == {"a"}, tree
        assert tree.children["a"] == [], tree
        assert set(turns) == {"a"}, turns

    def it_splices_a_pass_through_preserving_sibling_order(self):
        # the spliced-in child takes its parent's place among the siblings,
        # so reply order still reflects the source's fork order
        tree = make_tree(
            {"p": "", "x": "p", "s": "p", "y": "p", "c": "s"}, current="y"
        )
        turns = {nid: turn(nid) for nid in ["p", "x", "y", "c"]}
        tree, turns = normalize_turnless(tree, turns, turn)
        assert tree.children["p"] == ["x", "c", "y"], tree
        assert tree.parent_of["c"] == "p", tree

    def it_splices_a_chain_of_pass_throughs(self):
        tree = make_tree({"s1": "", "s2": "s1", "c": "s2"}, current="c")
        turns = {"c": turn("c")}
        tree, turns = normalize_turnless(tree, turns, turn)
        assert set(tree.parent_of) == {"c"}, tree
        assert tree.children[""] == ["c"], tree

    def it_materializes_a_turn_at_a_turnless_fork(self):
        # a fork needs a numbered anchor for replies/backrefs; make_turn
        # supplies the synthetic heading
        tree = make_tree({"s": "", "x": "s", "y": "s"}, current="y")
        turns = {"x": turn("x"), "y": turn("y")}
        tree, turns = normalize_turnless(tree, turns, turn)
        assert set(tree.parent_of) == {"s", "x", "y"}, tree
        assert turns["s"] == turn("s"), turns


class DescribeVersionStatus:
    """A fork the provider named but didn't send -- chatgpt's paginated
    endpoints mark an edited turn `has_versions` without carrying the
    superseded text. The reader is told the gap exists rather than shown a
    straight line."""

    def it_names_an_uncaptured_fork_in_the_priors_line(self):
        tree = make_tree({"a": "", "b": "a"}, current="b", uncaptured={"b"})
        markdown, _ = render_tree(tree, {"a": turn("a"), "b": turn("b")})
        assert "*prior revisions: not captured*" in markdown, markdown

    def it_leaves_an_unflagged_turn_alone(self):
        tree = make_tree({"a": "", "b": "a"}, current="b")
        markdown, _ = render_tree(tree, {"a": turn("a"), "b": turn("b")})
        assert "not captured" not in markdown, markdown

    def it_lists_captured_and_uncaptured_priors_together(self):
        tree = make_tree({"p": "", "x": "p", "y": "p"}, current="y", uncaptured={"y"})
        turns = {nid: turn(nid) for nid in ["p", "x", "y"]}
        markdown, _ = render_tree(tree, turns)
        assert "*prior revisions: 001, not captured*" in markdown, markdown

    def it_keeps_the_superseded_pointer_alongside(self):
        # a captured dead branch that itself has uncaptured siblings: both
        # facts are true of it, and neither displaces the other
        tree = make_tree({"p": "", "x": "p", "y": "p"}, current="y", uncaptured={"x"})
        turns = {nid: turn(nid) for nid in ["p", "x", "y"]}
        markdown, _ = render_tree(tree, turns)
        assert "*superseded by: 002 · prior revisions: not captured*" in markdown, markdown

    def it_survives_turnless_normalization(self):
        tree = make_tree({"s": "", "b": "s"}, current="b", uncaptured={"b"})
        tree, turns = normalize_turnless(tree, {"b": turn("b")}, turn)
        markdown, _ = render_tree(tree, turns)
        assert "*prior revisions: not captured*" in markdown, markdown
