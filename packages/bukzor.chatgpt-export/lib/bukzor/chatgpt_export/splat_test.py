"""Tests for bukzor.chatgpt_export.splat."""

from collections.abc import Mapping
from decimal import Decimal

from . import splat as M
from .types import JsonObj


class DescribeMessage:
    def it_formats_as_timestamp_role_uuid(self):
        msg = M.Message(
            uuid="abc123",
            timestamp=Decimal("1700000000.0"),
            role="user",
            text_content=None,
            raw={},
        )
        result = str(msg)
        assert "user" in result
        assert "abc123" in result
        assert result.endswith(".user.abc123")

    def it_preserves_nanoseconds(self):
        msg = M.Message(
            uuid="x",
            timestamp=Decimal("1234567890.123456789"),
            role="assistant",
            text_content=None,
            raw={},
        )
        assert ",123456789" in str(msg)


class DescribeConversationLink:
    def it_formats_as_seq_dot_role(self):
        msg = M.Message(uuid="x", timestamp=Decimal(0), role="user", text_content=None, raw={})
        link = M.ConversationLink(path=(), seq=95, messages=[msg])
        assert str(link) == "095.user"

    def it_uses_shared_role_for_same_role_messages(self):
        m1 = M.Message(uuid="a", timestamp=Decimal(1), role="user", text_content=None, raw={})
        m2 = M.Message(uuid="b", timestamp=Decimal(2), role="user", text_content=None, raw={})
        link = M.ConversationLink(path=(), seq=5, messages=[m1, m2])
        assert link.role == "user"
        assert str(link) == "005.user"

    def it_uses_fork_for_mixed_role_messages(self):
        m1 = M.Message(uuid="a", timestamp=Decimal(1), role="user", text_content=None, raw={})
        m2 = M.Message(uuid="b", timestamp=Decimal(2), role="assistant", text_content=None, raw={})
        link = M.ConversationLink(path=(), seq=5, messages=[m1, m2])
        assert link.role == "fork"
        assert str(link) == "005.fork"


class DescribeFormatTimestamp:
    def it_formats_as_iso8601(self):
        result = M.format_timestamp(Decimal(0))
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

    def it_handles_root_messages_without_parent(self):
        mapping: JsonObj = {
            "root": {},
            "child": {"parent": "root"},
        }
        tree = M.build_tree(mapping)
        assert "root" in tree
        assert tree["root"] == ["child"]


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


class DescribeExtractTextContent:
    def it_joins_text_parts(self):
        raw: JsonObj = {
            "message": {
                "content": {
                    "content_type": "text",
                    "parts": ["Hello", "World"],
                }
            }
        }
        assert M.extract_text_content(raw) == "Hello\nWorld"

    def it_returns_none_when_no_message(self):
        assert M.extract_text_content({}) is None

    def it_returns_none_for_non_text_content(self):
        raw: JsonObj = {
            "message": {
                "content": {
                    "content_type": "code",
                    "parts": ["print('hi')"],
                }
            }
        }
        assert M.extract_text_content(raw) is None

    def it_returns_none_when_parts_are_empty(self):
        raw: JsonObj = {
            "message": {
                "content": {
                    "content_type": "text",
                    "parts": [],
                }
            }
        }
        assert M.extract_text_content(raw) is None

    def it_preserves_empty_string_parts(self):
        """Empty strings between parts should produce blank lines, not be dropped."""
        raw: JsonObj = {
            "message": {
                "content": {
                    "content_type": "text",
                    "parts": ["Hello", "", "World"],
                }
            }
        }
        assert M.extract_text_content(raw) == "Hello\n\nWorld"

    def it_returns_none_when_all_parts_are_none(self):
        """All-None parts means no text content, not empty string."""
        raw: JsonObj = {
            "message": {
                "content": {
                    "content_type": "text",
                    "parts": [None, None],
                }
            }
        }
        assert M.extract_text_content(raw) is None


class DescribePrepareMessage:
    def it_replaces_text_parts_with_placeholder(self):
        raw: JsonObj = {
            "message": {
                "content": {
                    "content_type": "text",
                    "parts": ["Hello", "World"],
                }
            }
        }
        result = M.prepare_message(raw, "Hello\nWorld")
        inner = result["message"]
        assert isinstance(inner, Mapping)
        content = inner["content"]
        assert isinstance(content, Mapping)
        assert content["parts"] == [M.MARKDOWN_PLACEHOLDER]

    def it_returns_raw_unchanged_when_no_text(self):
        raw: JsonObj = {"message": {"content": {"content_type": "code", "parts": ["x"]}}}
        result = M.prepare_message(raw, None)
        assert result is raw

    def it_does_not_mutate_original(self):
        raw: JsonObj = {
            "message": {
                "content": {
                    "content_type": "text",
                    "parts": ["Hello"],
                }
            }
        }
        M.prepare_message(raw, "Hello")
        inner = raw["message"]
        assert isinstance(inner, Mapping)
        content = inner["content"]
        assert isinstance(content, Mapping)
        assert content["parts"] == ["Hello"]


class DescribeFindRoots:
    def it_finds_messages_without_parent(self):
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


class DescribeEnumerateConversationLinks:
    def _make_messages(self, spec: dict[str, dict[str, object]]) -> dict[str, M.Message]:
        """Build messages from {id: {parent, ts, role}} shorthand."""
        messages: dict[str, M.Message] = {}
        for msg_id, info in spec.items():
            ts = info.get("ts", 0.0)
            assert isinstance(ts, (int, float))
            role = info.get("role", "unknown")
            assert isinstance(role, str)
            raw: JsonObj = {}
            if "parent" in info:
                parent = info["parent"]
                assert isinstance(parent, str)
                raw["parent"] = parent
            messages[msg_id] = M.Message(
                uuid=msg_id,
                timestamp=Decimal(str(ts)),
                role=role,
                text_content=None,
                raw=raw,
            )
        return messages

    def _make_mapping(self, spec: dict[str, dict[str, object]]) -> JsonObj:
        """Build a JsonObj mapping from {id: {parent, ts, role}} shorthand."""
        from .types import JsonValue

        mapping: dict[str, JsonValue] = {}
        for msg_id, info in spec.items():
            raw: dict[str, JsonValue] = {}
            if "parent" in info:
                parent = info["parent"]
                assert isinstance(parent, str)
                raw["parent"] = parent
            mapping[msg_id] = raw
        return mapping

    def it_yields_links_for_linear_chain(self):
        spec: dict[str, dict[str, object]] = {
            "root": {"ts": 1.0, "role": "root"},
            "a": {"parent": "root", "ts": 2.0, "role": "user"},
            "b": {"parent": "a", "ts": 3.0, "role": "assistant"},
        }
        messages = self._make_messages(spec)
        tree = M.build_tree(self._make_mapping(spec))
        links = list(M.enumerate_conversation_links("root", tree, messages, 0, ()))
        assert len(links) == 3
        assert [str(l) for l in links] == ["000.root", "001.user", "002.assistant"]
        assert all(l.path == () for l in links)
        assert links[0].messages[0] is messages["root"]
        assert links[1].messages[0] is messages["a"]
        assert links[2].messages[0] is messages["b"]

    def it_yields_fork_link_at_branch_point(self):
        spec: dict[str, dict[str, object]] = {
            "root": {"ts": 1.0, "role": "root"},
            "a": {"parent": "root", "ts": 2.0, "role": "user"},
            "b": {"parent": "root", "ts": 3.0, "role": "user"},
        }
        messages = self._make_messages(spec)
        tree = M.build_tree(self._make_mapping(spec))
        links = list(M.enumerate_conversation_links("root", tree, messages, 0, ()))
        # root link, fork link, then branch links
        fork_links = [l for l in links if len(l.messages) > 1]
        assert len(fork_links) == 1
        assert fork_links[0].seq == 1
        assert fork_links[0].role == "user"
        assert fork_links[0].messages[0] is messages["a"]
        assert fork_links[0].messages[1] is messages["b"]

    def it_nests_branch_paths(self):
        spec: dict[str, dict[str, object]] = {
            "root": {"ts": 1.0, "role": "root"},
            "a": {"parent": "root", "ts": 2.0, "role": "user"},
            "b": {"parent": "root", "ts": 3.0, "role": "user"},
        }
        messages = self._make_messages(spec)
        tree = M.build_tree(self._make_mapping(spec))
        links = list(M.enumerate_conversation_links("root", tree, messages, 0, ()))
        branch_links = [l for l in links if l.path != ()]
        assert len(branch_links) == 2
        # Each branch path starts with the fork link name
        for bl in branch_links:
            assert bl.path[0] == "001.user"
        assert branch_links[0].messages[0] is messages["a"]
        assert branch_links[1].messages[0] is messages["b"]
