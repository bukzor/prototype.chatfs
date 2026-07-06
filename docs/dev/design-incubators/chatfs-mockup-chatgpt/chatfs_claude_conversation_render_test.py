"""Regression tests for the renderer's pre-render tree pruning."""

from pathlib import Path

from chatfs_claude_conversation_render import load_turns, prune_bodiless_leaves
from chatfs_claude_types import ChatMessage, ContentBlock, Several


def msg(
    uuid: str,
    parent: str = "root",
    text: str = "",
    content: list[ContentBlock] | None = None,
) -> ChatMessage:
    """A chat_messages node, defaulting to bodiless (no text, no content)."""
    return {
        "uuid": uuid,
        "sender": "human",
        "parent_message_uuid": parent,
        "created_at": "2026-06-03T00:00:00Z",
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
