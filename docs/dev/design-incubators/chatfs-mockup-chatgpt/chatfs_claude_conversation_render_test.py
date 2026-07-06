"""Regression tests for the renderer: tree pruning, fork selection, and the
fork-fact markdown itself."""

from pathlib import Path
from textwrap import dedent

import pytest

from chatfs_claude_conversation_render import (
    Turn,
    live_ancestors,
    load_turns,
    primary_child,
    prune_bodiless_leaves,
    render_conversation,
)
from chatfs_claude_types import ChatMessage, ContentBlock, Several


def msg(
    uuid: str,
    parent: str = "root",
    text: str = "",
    content: list[ContentBlock] | None = None,
    created_at: str = "2026-06-03T00:00:00Z",
) -> ChatMessage:
    """A chat_messages node, defaulting to bodiless (no text, no content)."""
    return {
        "uuid": uuid,
        "sender": "human",
        "parent_message_uuid": parent,
        "created_at": created_at,
        "text": text,
        "content": content or [],
    }


def uuids(messages: Several[ChatMessage]) -> list[str]:
    return [m["uuid"] for m in messages]


class DescribePruneBodilessLeaves:
    def it_drops_a_contentless_canceled_leaf(self):
        # a user_canceled retry: a .json on disk, no .md, no children — keeping it
        # would fabricate a fork whose sibling has no turn to number.
        msgs = (msg("a", text="hi"), msg("cancel", parent="a"))
        assert uuids(prune_bodiless_leaves(msgs, rendered={"a"})) == ["a"]

    def it_keeps_every_rendered_message(self):
        msgs = (msg("a", text="hi"), msg("b", parent="a", text="bye"))
        assert uuids(prune_bodiless_leaves(msgs, rendered={"a", "b"})) == ["a", "b"]

    def it_keeps_a_bodiless_node_that_still_has_content(self):
        # bodiless-but-has-content is a splat/render bug, not a cancel: retain it
        # so the caller's body-coverage assertion fails loudly.
        msgs = (
            msg("a", text="hi"),
            msg("b", parent="a", content=[{"type": "text", "text": "stray"}]),
        )
        kept = prune_bodiless_leaves(msgs, rendered={"a"})
        assert {m["uuid"] for m in kept} == {"a", "b"}, kept

    def it_prunes_a_chain_of_bodiless_nodes(self):
        # a cancel whose only child is another cancel: the leaf falls first,
        # which leaves its parent childless and contentless -- it must fall too.
        msgs = (msg("a", text="hi"), msg("b", parent="a"), msg("c", parent="b"))
        assert uuids(prune_bodiless_leaves(msgs, rendered={"a"})) == ["a"]

    def it_keeps_a_bodiless_non_leaf(self):
        # an empty node with a child can't be dropped without re-parenting: retain
        # it so the missing-body check fires rather than silently restructuring.
        msgs = (
            msg("a", text="hi"),
            msg("empty", parent="a"),
            msg("c", parent="empty", text="hi"),
        )
        kept = prune_bodiless_leaves(msgs, rendered={"a", "c"})
        assert {m["uuid"] for m in kept} == {"a", "empty", "c"}, kept


class DescribePrimaryChild:
    def it_breaks_created_at_ties_toward_the_last_sibling(self):
        # equal timestamps happen at claude's second resolution; "latest" then
        # means the one the source listed later
        msgs = (msg("a", text="x"), msg("b", text="y"))
        by_uuid = {m["uuid"]: m for m in msgs}
        assert primary_child(["a", "b"], set[str](), by_uuid) == "b"


class DescribeLiveAncestors:
    def it_rejects_a_current_leaf_missing_from_the_tree(self):
        # a pruned bodiless cancel could be the recorded current leaf; silently
        # returning an empty live set would demote the whole trunk to <-latest
        by_uuid = {m["uuid"]: m for m in (msg("a", text="x"),)}
        with pytest.raises(AssertionError):
            _ = live_ancestors(by_uuid, "gone")


class DescribeRenderConversation:
    def it_renders_each_branch_as_one_island_with_fork_facts(self):
        # trunk a->b with two abandoned attempts off a: d1 (whose own retry
        # forked again: n1 abandoned, d2 kept) and e1. Exercises every divider
        # kind: trunk blank, aside opening, nested aside opening and resuming
        # inside one island, and the rule between sibling attempts.
        msgs = (
            msg("a", text="body a"),
            msg("d1", parent="a", text="body d1", created_at="2026-06-03T00:00:01Z"),
            msg("e1", parent="a", text="body e1", created_at="2026-06-03T00:00:02Z"),
            msg("b", parent="a", text="body b", created_at="2026-06-03T00:00:03Z"),
            msg("n1", parent="d1", text="body n1", created_at="2026-06-03T00:00:04Z"),
            msg("d2", parent="d1", text="body d2", created_at="2026-06-03T00:00:05Z"),
        )
        turns = {m["uuid"]: Turn("human", "T", "L", m["text"]) for m in msgs}
        markdown, count = render_conversation(msgs, "b", turns)
        assert count == 6
        assert markdown == dedent("""\
            # [000 · human · T](L)

            body a

            *replies: 001, 004, 005 ←live*

            > # [001 · human · T](L)
            >
            > *superseded by: 005*
            >
            > body d1
            >
            > *replies: 002, 001/003 ←latest*
            >
            > > # [002 · human · T](L)
            > >
            > > *superseded by: 001/003*
            > >
            > > body n1
            >
            > # [001/003 · human · T](L) (re: 001)
            >
            > *prior revisions: 002*
            >
            > body d2

            ---

            > # [004 · human · T](L) (re: 000)
            >
            > *superseded by: 005*
            >
            > body e1

            # [005 · human · T](L) (re: 000)

            *prior revisions: 001, 004*

            body b
            """)


class DescribeLoadTurns:
    def write_message(self, tmp_path: Path, stem: str):
        _ = (tmp_path / f"{stem}.json").write_text("{}\n")
        _ = (tmp_path / f"{stem}.md").write_text("hi\n")

    def it_truncates_the_heading_time_to_the_minute(self, tmp_path: Path):
        self.write_message(tmp_path, "2026-05-10T15:41:14,405121000-0500.human.abc")
        turns = load_turns(tmp_path)
        assert turns["abc"].time == "2026-05-10T15:41", turns

    def it_accepts_mixed_offsets(self, tmp_path: Path):
        # a conversation spanning a DST change has mixed offsets -- normal for
        # long-lived chats, since each basename carries the offset in effect at
        # that message's moment. Headings show per-message wall-clock time; the
        # link keeps the offset for anyone who needs it.
        self.write_message(tmp_path, "2026-03-08T01:59:00,000000000-0600.human.abc")
        self.write_message(tmp_path, "2026-03-08T03:01:00,000000000-0500.assistant.xyz")
        turns = load_turns(tmp_path)
        assert turns["abc"].time == "2026-03-08T01:59", turns
        assert turns["xyz"].time == "2026-03-08T03:01", turns
