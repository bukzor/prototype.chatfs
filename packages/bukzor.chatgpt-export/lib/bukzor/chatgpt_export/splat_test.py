"""Tests for bukzor.chatgpt_export.splat."""

from decimal import Decimal

from . import splat as M
from .types import JsonObj, JsonValue


class DescribeFormatTimestamp:
    def it_formats_as_iso8601(self):
        result = M.format_timestamp(Decimal(0))
        # Should contain date, time, and timezone offset
        assert "1970" in result or "1969" in result  # depends on local tz
        assert "T" in result

    def it_preserves_nanoseconds_with_decimal(self):
        result = M.format_timestamp(Decimal("1234567890.123456789"))
        assert ",123456789" in result

    def it_preserves_nanoseconds_with_string(self):
        result = M.format_timestamp("1234567890.123456789")
        assert ",123456789" in result


class DescribeBuildTree:
    def it_maps_parents_to_children(self):
        mapping: JsonObj = {
            "root": {},
            "child1": {"parent": "root"},
            "child2": {"parent": "root"},
        }
        tree = M.build_tree(mapping)
        assert set(tree["root"]) == {"child1", "child2"}

    def it_handles_root_nodes_without_parent(self):
        mapping: JsonObj = {
            "root": {},
            "child": {"parent": "root"},
        }
        tree = M.build_tree(mapping)
        # Root has no parent, so it shouldn't appear as a key from parenting
        assert "root" in tree  # root is a parent
        assert tree["root"] == ["child"]


class DescribeGetNodeTimestamp:
    def it_extracts_create_time(self):
        node: JsonObj = {"message": {"create_time": 1700000000.0}}
        assert M.get_node_timestamp(node) == 1700000000.0

    def it_returns_default_when_no_message(self):
        assert M.get_node_timestamp({}) == 0.0
        assert M.get_node_timestamp({}, default=42.0) == 42.0

    def it_returns_default_when_create_time_is_null(self):
        node: JsonObj = {"message": {"create_time": None}}
        assert M.get_node_timestamp(node) == 0.0


class DescribeComputeMinTimestamp:
    def it_finds_earliest_timestamp(self):
        mapping: JsonObj = {
            "a": {"message": {"create_time": 300.0}},
            "b": {"message": {"create_time": 100.0}},
            "c": {"message": {"create_time": 200.0}},
        }
        assert M.compute_min_timestamp(mapping) == 100.0

    def it_returns_zero_when_no_timestamps(self):
        mapping: JsonObj = {
            "a": {},
            "b": {"message": {}},
            "c": {"message": {"create_time": None}},
        }
        assert M.compute_min_timestamp(mapping) == 0.0


class DescribeGetNodeRole:
    def it_extracts_role_from_author(self):
        node: JsonObj = {"message": {"author": {"role": "assistant"}}}
        assert M.get_node_role(node) == "assistant"

    def it_returns_root_when_no_message(self):
        assert M.get_node_role({}) == "root"

    def it_returns_unknown_when_no_author(self):
        assert M.get_node_role({"message": {}}) == "unknown"


class DescribeExtractTextContent:
    def it_joins_text_parts(self):
        node: JsonObj = {
            "message": {
                "content": {
                    "content_type": "text",
                    "parts": ["Hello", "World"],
                }
            }
        }
        assert M.extract_text_content(node) == "Hello\nWorld"

    def it_returns_none_when_no_message(self):
        assert M.extract_text_content({}) is None

    def it_returns_none_for_non_text_content(self):
        node: JsonObj = {
            "message": {
                "content": {
                    "content_type": "code",
                    "parts": ["print('hi')"],
                }
            }
        }
        assert M.extract_text_content(node) is None

    def it_returns_none_when_parts_are_empty(self):
        node: JsonObj = {
            "message": {
                "content": {
                    "content_type": "text",
                    "parts": [],
                }
            }
        }
        assert M.extract_text_content(node) is None

    def it_preserves_empty_string_parts(self):
        """Empty strings between parts should produce blank lines, not be dropped."""
        node: JsonObj = {
            "message": {
                "content": {
                    "content_type": "text",
                    "parts": ["Hello", "", "World"],
                }
            }
        }
        assert M.extract_text_content(node) == "Hello\n\nWorld"


class DescribeNodeFilename:
    def it_combines_timestamp_role_and_id(self):
        result = M.node_filename("abc123", Decimal("1700000000.0"), "user")
        assert "user" in result
        assert "abc123" in result
        assert result.endswith(".user.abc123")


class DescribeFindRoots:
    def it_finds_nodes_without_parent(self):
        mapping: JsonObj = {
            "root": {},
            "child": {"parent": "root"},
        }
        assert M.find_roots(mapping) == ["root"]

    def it_returns_empty_list_when_all_have_parents(self):
        mapping: JsonObj = {
            "a": {"parent": "x"},
            "b": {"parent": "y"},
        }
        assert M.find_roots(mapping) == []


def _mapping_with_timestamps(nodes: dict[str, dict[str, JsonValue]]) -> JsonObj:
    """Build a mapping from {id: {parent, timestamp}} shorthand."""
    mapping: JsonObj = {}
    for node_id, info in nodes.items():
        node: JsonObj = {}
        if "parent" in info:
            node["parent"] = info["parent"]
        if "ts" in info:
            node["message"] = {"create_time": info["ts"]}
        mapping[node_id] = node
    return mapping


class DescribeEnumerateConversations:
    def it_yields_single_conversation_for_linear_tree(self):
        mapping = _mapping_with_timestamps({
            "root": {"ts": 1.0},
            "a": {"parent": "root", "ts": 2.0},
            "b": {"parent": "a", "ts": 3.0},
        })
        tree = M.build_tree(mapping)
        convos = list(M.enumerate_conversations(mapping, tree, "root", "root", [], 1.0))
        assert len(convos) == 1
        assert convos[0].path == ["root", "a", "b"]
        assert convos[0].id == "root"

    def it_yields_multiple_conversations_at_forks(self):
        mapping = _mapping_with_timestamps({
            "root": {"ts": 1.0},
            "a": {"parent": "root", "ts": 2.0},
            "b": {"parent": "root", "ts": 3.0},
        })
        tree = M.build_tree(mapping)
        convos = list(M.enumerate_conversations(mapping, tree, "root", "root", [], 1.0))
        assert len(convos) == 2

    class WhenForking:
        def it_continues_original_id_on_earliest_child(self):
            mapping = _mapping_with_timestamps({
                "root": {"ts": 1.0},
                "early": {"parent": "root", "ts": 2.0},
                "late": {"parent": "root", "ts": 3.0},
            })
            tree = M.build_tree(mapping)
            convos = list(M.enumerate_conversations(mapping, tree, "root", "root", [], 1.0))
            earliest_conv = [c for c in convos if "early" in c.path][0]
            assert earliest_conv.id == "root"

        def it_assigns_fork_id_to_later_children(self):
            mapping = _mapping_with_timestamps({
                "root": {"ts": 1.0},
                "early": {"parent": "root", "ts": 2.0},
                "late": {"parent": "root", "ts": 3.0},
            })
            tree = M.build_tree(mapping)
            convos = list(M.enumerate_conversations(mapping, tree, "root", "root", [], 1.0))
            later_conv = [c for c in convos if "late" in c.path][0]
            assert later_conv.id == "late"
