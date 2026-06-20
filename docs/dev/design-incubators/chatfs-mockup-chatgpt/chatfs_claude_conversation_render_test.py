"""Regression tests for the renderer's pre-render tree pruning."""

from chatfs_claude_conversation_render import prune_bodiless_leaves
from chatfs_claude_types import ChatMessage, Several
from chatfs_json import JsonValue


def msg(
    uuid: str,
    parent: str = "root",
    text: str = "",
    content: list[JsonValue] | None = None,
) -> ChatMessage:
    """A chat_messages node, defaulting to bodiless (no text, no content)."""
    return {
        "uuid": uuid,
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
        msgs = (msg("a", text="hi"), msg("b", parent="a", content=[{"type": "text"}]))
        kept = prune_bodiless_leaves(msgs, rendered={"a"})
        assert {m["uuid"] for m in kept} == {"a", "b"}, kept

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
