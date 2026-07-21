"""Regression tests exercising chatgpt's real `mapping` shape -- the generic
tree algorithms are pinned abstractly in `chatfs/render_test.py`; these tests
pin chatgpt's own integration: `build_tree`'s float `create_time` extraction,
and `make_turn`'s stem-based synthetic anchor."""

from chatfs.provider.chatgpt.conversation.render import (
    Stem,
    build_tree,
    make_turn,
    render_conversation,
)
from chatfs.provider.chatgpt.types import Conversation, Node
from chatfs.render import Turn, primary_child


def node(parent: str | None, children: list[str], create_time: float | None) -> Node:
    """A `mapping[uuid]` entry -- turn-less when `create_time` is None."""
    return {
        "parent": parent,
        "children": children,
        "message": None if create_time is None else {"create_time": create_time},
    }


def stem(uuid: str, role: str, content_type: str = "text") -> Stem:
    ts = "2026-06-01T12:00:00,000000000-0500"
    return Stem(f"{ts}.{role}.{uuid}.{content_type}", ts, role, content_type)


class DescribeBuildTree:
    def it_extracts_floating_point_create_time_for_tie_breaking(self):
        # chatgpt's create_time is unix-epoch float (sub-second precision), unlike
        # claude's second-truncated ISO string -- a genuine tie is the same float
        conversation: Conversation = {
            "mapping": {
                "p": node(None, ["x", "y"], create_time=1000.0),
                "x": node("p", [], create_time=1751328000.123456),
                "y": node("p", [], create_time=1751328000.123456),
            },
            "current_node": "p",
        }
        tree = build_tree(conversation)
        assert primary_child(tree.children["p"], set[str](), tree.created) == "y"


class DescribeRenderConversation:
    def it_materializes_a_turn_at_a_turnless_fork(self):
        # a system placeholder (no message) with two replying children: the
        # generic algorithm is pinned in chatfs/render_test.py; this pins that
        # chatgpt's own `make_turn` produces a correctly shaped anchor -- role
        # and note read from the parsed stem, body empty, link to the .json
        conversation: Conversation = {
            "mapping": {
                "sys": node(None, ["a", "b"], create_time=None),
                "a": node("sys", [], create_time=1751328000.0),
                "b": node("sys", [], create_time=1751328001.0),
            },
            "current_node": "b",
        }
        stems = {
            "sys": stem("sys", "system"),
            "a": stem("a", "assistant"),
            "b": stem("b", "assistant"),
        }
        turns = {
            "a": Turn("assistant", "T", "L", "body a"),
            "b": Turn("assistant", "T", "L", "body b"),
        }
        markdown, count = render_conversation(conversation, stems, turns)
        assert count == 3
        assert "[000 · system · 2026-06-01T12:00](messages/2026-06-01T12:00:00,000000000-0500.system.sys.text.json)" in markdown, markdown


class DescribeMakeTurn:
    def it_names_the_json_record_not_the_missing_markdown(self):
        # the synthetic anchor has no body to link -- pointing at the .json
        # keeps the heading a real, dereferenceable file even with no .md
        s = stem("sys", "system", "text")
        turn = make_turn("sys", {"sys": s})
        assert turn == Turn("system", "2026-06-01T12:00", f"messages/{s.stem}.json", "", "")

    def it_carries_the_content_type_note(self):
        turn = make_turn("t", {"t": stem("t", "assistant", "thoughts")})
        assert turn.note == "thoughts"
