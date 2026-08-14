"""Regression tests for splat's content-block extraction."""

import pytest

from chatfs.provider.claude.conversation.splat import extract_text
from chatfs.provider.claude.types import (
    TextBlock,
    TokenBudgetBlock,
    ToolResultBlock,
    ToolUseBlock,
)


class DescribeExtractText:
    def it_drops_a_token_budget_block(self):
        # an internal budget checkpoint claude.ai's export interleaves around
        # tool calls -- captured 2025-12-01 between a tool_result and the
        # following thinking block. Timestamps only, nothing to show.
        block: TokenBudgetBlock = {
            "type": "token_budget",
            "start_timestamp": "2025-12-01T19:41:41.570375Z",
            "stop_timestamp": "2025-12-01T19:41:41.570375Z",
        }
        assert extract_text((block,)) == ""

    def it_renders_a_tool_use_canceled_before_its_result(self):
        # user_canceled mid-call: claude.ai marks this the same way it marks
        # a bodiless user_canceled retry -- a hollow trailing text block --
        # captured 2025-07-16 from a launch_extended_search_task the user
        # canceled before any tool_result arrived.
        use: ToolUseBlock = {
            "type": "tool_use",
            "name": "launch_extended_search_task",
            "input": {"command": "research x"},
            "message": "launch_extended_search_task",
        }
        hollow: TextBlock = {"type": "text", "text": ""}
        text = extract_text((use, hollow))
        assert "launch_extended_search_task" in text
        assert "canceled" in text

    def it_falls_back_to_name_when_tool_use_has_no_message(self):
        # observed 2025-09-16: an `artifacts` tool_use with no `message` key
        # at all (every other tool_use in the same capture had one).
        use: ToolUseBlock = {
            "type": "tool_use",
            "name": "artifacts",
            "input": {"id": "x", "command": "create"},
        }
        result: ToolResultBlock = {
            "type": "tool_result",
            "content": "ok",
            "is_error": False,
        }
        assert "artifacts" in extract_text((use, result))

    def it_accepts_a_web_fetch_with_a_token_limit(self):
        # `text_content_token_limit` is an optional extra key alongside `url`
        # -- captured 2025-12 requesting a capped excerpt of a docs page.
        use: ToolUseBlock = {
            "type": "tool_use",
            "name": "web_fetch",
            "input": {
                "url": "https://docs.claude.com/en/docs/claude-code",
                "text_content_token_limit": "5000",
            },
            "message": "web_fetch",
        }
        result: ToolResultBlock = {
            "type": "tool_result",
            "content": "fetched",
            "is_error": False,
        }
        text = extract_text((use, result))
        assert "docs.claude.com" in text
        assert "fetched" in text

    def it_pairs_a_tool_use_and_result_by_position_alone(self):
        # claude.ai's own export carries no id/tool_use_id on these blocks
        # (unlike the Messages API) -- captured 2025-12-01 from a live
        # conversation using the built-in web_search tool. Adjacency is the
        # only correlation available, and it's enough.
        use: ToolUseBlock = {
            "type": "tool_use",
            "name": "web_search",
            "input": {"query": "x"},
            "message": "Searching the web",
        }
        result: ToolResultBlock = {
            "type": "tool_result",
            "content": "no results",
            "is_error": False,
        }
        assert "no results" in extract_text((use, result))

    def it_rejects_a_trailing_unpaired_tool_use(self):
        # an interrupted tool call: tool_use is the final block, no result ever
        # arrived -- must fail with the mispairing message, not an IndexError.
        block: ToolUseBlock = {
            "type": "tool_use",
            "name": "web_search",
            "input": {"query": "x"},
            "message": "",
        }
        with pytest.raises(
            AssertionError, match="tool_use without following tool_result"
        ):
            _ = extract_text((block,))
