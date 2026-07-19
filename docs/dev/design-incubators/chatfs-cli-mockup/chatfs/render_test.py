"""Tests for the shared turn-less tree repair; the render pipeline itself is
pinned end-to-end by the claude renderer's golden test."""

from chatfs_render import ConversationTree, Turn, normalize_turnless


def turn(nid: str) -> Turn:
    return Turn("human", "T", "L", f"body {nid}")


def make_tree(parent_of: dict[str, str], current: str) -> ConversationTree:
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
