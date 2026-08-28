"""Tests for chatfs.provider.chatgpt.conversation.assemble."""

import pytest

from chatfs.provider.chatgpt.json import JsonObj, JsonValue

from . import assemble as M

CONV = "https://chatgpt.com/backend-api/conversations/0badc0de"


def message(id_: str) -> JsonObj:
    return {"id": id_, "author": {"role": "user"}, "content": {"content_type": "text"}}


def page(*ids: str, has_previous: bool) -> JsonObj:
    return {
        "messages": [message(i) for i in ids],
        "page_info": {
            "start_cursor": ids[0],
            "end_cursor": ids[-1],
            "has_previous_page": has_previous,
            "has_next_page": True,
        },
    }


def record(url: str, body: JsonObj) -> JsonObj:
    return {"url": url, "body": body}


def head_page(*ids: str, has_previous: bool) -> JsonObj:
    """The conversation endpoint's own body: identity fields plus the newest page."""
    return {
        "conversation_id": "0badc0de",
        "title": "a title",
        "current_node": ids[-1],
        **page(*ids, has_previous=has_previous),
    }


class DescribeAssemble:
    def it_passes_through_a_whole_document(self):
        doc: JsonObj = {"mapping": {"a": {"id": "a"}}, "current_node": "a"}
        assert M.assemble([record(CONV, doc)]) == doc

    def it_links_a_single_page_into_a_mapping(self):
        result = M.assemble([record(CONV, head_page("a", "b", has_previous=False))])
        assert result["mapping"] == {
            "a": {"id": "a", "message": message("a"), "parent": None, "children": ["b"]},
            "b": {"id": "b", "message": message("b"), "parent": "a", "children": []},
        }

    def it_drops_the_transport_fields(self):
        result = M.assemble([record(CONV, head_page("a", has_previous=False))])
        assert set(result) == {"conversation_id", "title", "current_node", "mapping"}

    def it_chains_older_pages_ahead_of_the_newest(self):
        result = M.assemble(
            [
                record(CONV, head_page("c", "d", has_previous=True)),
                record(f"{CONV}/messages?before=c", page("a", "b", has_previous=False)),
            ]
        )
        mapping = result["mapping"]
        assert isinstance(mapping, dict), mapping
        assert list(mapping) == ["a", "b", "c", "d"]
        assert mapping["b"] == {
            "id": "b",
            "message": message("b"),
            "parent": "a",
            "children": ["c"],
        }

    def it_raises_when_an_older_page_is_missing(self):
        with pytest.raises(AssertionError, match="scroll to the top"):
            _ = M.assemble([record(CONV, head_page("c", "d", has_previous=True))])

    def it_merges_pass_through_lists_across_pages(self):
        older: JsonObj = {
            **page("a", has_previous=False),
            "safe_urls": ["http://one", "http://two"],
        }
        head: JsonObj = {
            **head_page("b", has_previous=True),
            "safe_urls": ["http://two", "http://three"],
        }
        result = M.assemble([record(CONV, head), record(f"{CONV}/messages?before=b", older)])
        assert result["safe_urls"] == ["http://one", "http://two", "http://three"]

    def it_raises_when_a_message_id_repeats_across_pages(self):
        with pytest.raises(AssertionError, match="duplicate"):
            _ = M.assemble(
                [
                    record(CONV, head_page("a", "b", has_previous=True)),
                    record(f"{CONV}/messages?before=a", page("a", has_previous=False)),
                ]
            )

    def it_prefers_the_last_response_for_a_repeated_page(self):
        stale = {**head_page("a", has_previous=False), "title": "stale"}
        result = M.assemble(
            [record(CONV, stale), record(CONV, head_page("a", has_previous=False))]
        )
        assert result["title"] == "a title"


class DescribeBeforeCursor:
    def it_reads_the_pagination_link_from_the_query(self):
        assert M.before_cursor(f"{CONV}/messages?before=a&num_turns=10") == "a"

    def it_is_none_without_one(self):
        assert M.before_cursor(f"{CONV}?include_has_versions=true") is None


class DescribeLinkMessages:
    def it_makes_one_root(self):
        mapping = M.link_messages([message("a"), message("b")])
        roots: list[JsonValue] = [
            node for node in mapping.values() if isinstance(node, dict) and node["parent"] is None
        ]
        assert len(roots) == 1
