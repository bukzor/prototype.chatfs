"""Regression tests for the renderer: tree pruning, fork selection, and the
fork-fact markdown itself."""

from pathlib import Path
from textwrap import dedent

import pytest

from chatfs.provider.claude.conversation.render import (
    build_tree,
    load_turns,
    normalize_bodiless_nodes,
    render_conversation,
)
from chatfs.provider.claude.types import ChatMessage, ContentBlock, Several
from chatfs.render import Turn, live_ancestors, primary_child


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


class DescribeNormalizeBodilessNodes:
    def it_drops_a_contentless_canceled_leaf(self):
        # a user_canceled retry: a .json on disk, no .md, no children — keeping it
        # would fabricate a fork whose sibling has no turn to number.
        msgs = (msg("a", text="hi"), msg("cancel", parent="a"))
        assert uuids(normalize_bodiless_nodes(msgs, rendered={"a"})) == ["a"]

    def it_keeps_every_rendered_message(self):
        msgs = (msg("a", text="hi"), msg("b", parent="a", text="bye"))
        assert uuids(normalize_bodiless_nodes(msgs, rendered={"a", "b"})) == ["a", "b"]

    def it_keeps_a_bodiless_node_that_still_has_content(self):
        # bodiless-but-has-content is a splat/render bug, not a cancel: retain it
        # so the caller's body-coverage assertion fails loudly.
        msgs = (
            msg("a", text="hi"),
            msg("b", parent="a", content=[{"type": "text", "text": "stray"}]),
        )
        kept = normalize_bodiless_nodes(msgs, rendered={"a"})
        assert {m["uuid"] for m in kept} == {"a", "b"}, kept

    def it_prunes_a_chain_of_bodiless_nodes(self):
        # a cancel whose only child is another cancel: the leaf falls first,
        # which leaves its parent childless and contentless -- it must fall too.
        msgs = (msg("a", text="hi"), msg("b", parent="a"), msg("c", parent="b"))
        assert uuids(normalize_bodiless_nodes(msgs, rendered={"a"})) == ["a"]

    def it_splices_a_bodiless_non_leaf_with_one_child(self):
        # claude.ai's tree can chain straight through a `user_canceled` retry:
        # the next real message parents off the cancel, not off the cancel's
        # own parent. Reparent the child and drop the cancel, so it doesn't
        # fabricate a fork whose only "sibling" is itself.
        msgs = (
            msg("a", text="hi"),
            msg("empty", parent="a"),
            msg("c", parent="empty", text="hi"),
        )
        kept = normalize_bodiless_nodes(msgs, rendered={"a", "c"})
        assert {m["uuid"]: m["parent_message_uuid"] for m in kept} == {"a": "root", "c": "a"}, kept


class DescribePrimaryChild:
    def it_breaks_creation_time_ties_toward_the_last_sibling(self):
        # equal timestamps happen at claude's second resolution; "latest" then
        # means the one the source listed later
        assert primary_child(["a", "b"], set[str](), {"a": 1.0, "b": 1.0}) == "b"


class DescribeLiveAncestors:
    def it_rejects_a_current_leaf_missing_from_the_tree(self):
        # a pruned bodiless cancel could be the recorded current leaf; silently
        # returning an empty live set would demote the whole trunk to <-latest
        tree = build_tree((msg("a", text="x"),), current="gone")
        with pytest.raises(AssertionError):
            _ = live_ancestors(tree)


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

    def it_renders_past_a_canceled_retry_with_no_assertion_failure(self):
        # regression for a real capture (2026-05-07): a `user_canceled`
        # assistant turn -- one empty text content block, no .md -- sat
        # mid-chain, its own reply continuing straight through it. Splicing
        # it out is what lets set(turns) == set(tree.parent_of) hold.
        msgs = (
            msg("a", text="body a"),
            msg("cancel", parent="a", content=[{"type": "text", "text": ""}]),
            msg("b", parent="cancel", text="body b", created_at="2026-06-03T00:00:01Z"),
        )
        turns = {m["uuid"]: Turn("human", "T", "L", m["text"]) for m in msgs if m["text"]}
        markdown, count = render_conversation(msgs, "b", turns)
        assert count == 2
        assert markdown == dedent("""\
            # [000 · human · T](L)

            body a

            # [001 · human · T](L)

            body b
            """)

    def it_renders_when_the_current_leaf_was_pruned(self):
        # regression for a real capture (2026-06-03,
        # cdacc3dc-fcdf-4871-b605-061e542c2407): the conversation's
        # `current_leaf_message_uuid` named a trailing assistant message with
        # an empty `content` -- exactly what normalize_bodiless_nodes drops --
        # so the live leaf was gone by the time live_ancestors looked for it.
        msgs = (
            msg("a", text="body a"),
            msg("b", parent="a", text="body b", created_at="2026-06-03T00:00:01Z"),
            msg("empty", parent="b", created_at="2026-06-03T00:00:02Z"),
        )
        turns = {m["uuid"]: Turn("human", "T", "L", m["text"]) for m in msgs if m["text"]}
        markdown, count = render_conversation(msgs, "empty", turns)
        assert count == 2
        assert "body b" in markdown

    def it_renders_nothing_when_every_message_was_pruned(self):
        msgs = (msg("empty"),)
        assert render_conversation(msgs, "empty", {}) == ("", 0)


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
