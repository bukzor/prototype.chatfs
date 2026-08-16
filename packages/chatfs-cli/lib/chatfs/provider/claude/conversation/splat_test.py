"""Regression tests for splat's content-block extraction."""

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

    def it_pairs_a_lone_tool_use_and_result_by_position_alone(self):
        # some captures carry no id/tool_use_id on these blocks at all
        # -- captured 2025-12-01 from a live conversation using the built-in
        # web_search tool. One use and one result can only mean each other.
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

    def it_renders_a_trailing_tool_use_with_no_result(self):
        # an interrupted tool call: tool_use is the final block, no result ever
        # arrived. The request is all the capture holds, so it's all we render
        # -- losing the whole conversation's markdown over it would be the
        # worse trade (technical-policy.kb/zero-data-loss...).
        block: ToolUseBlock = {
            "type": "tool_use",
            "name": "web_search",
            "input": {"query": "x"},
            "message": "",
        }
        text = extract_text((block,))
        assert "x" in text
        assert "request" in text


class DescribeParallelToolCalls:
    """claude.ai runs several tools at once: N `tool_use` then N `tool_result`."""

    def it_pairs_a_parallel_batch_by_id(self):
        uses: list[ToolUseBlock] = [
            {"type": "tool_use", "name": "web_search", "id": "toolu_A", "input": {"query": "alpha"}},
            {"type": "tool_use", "name": "web_search", "id": "toolu_B", "input": {"query": "beta"}},
        ]
        results: list[ToolResultBlock] = [
            # deliberately out of call order: id pairing must not follow position
            {"type": "tool_result", "tool_use_id": "toolu_B", "content": "BBB", "is_error": False},
            {"type": "tool_result", "tool_use_id": "toolu_A", "content": "AAA", "is_error": False},
        ]
        text = extract_text((*uses, *results))
        # each query captions its own result, in call order
        assert text.index("alpha") < text.index("AAA") < text.index("beta") < text.index("BBB")

    def it_reads_the_id_from_the_input_when_there_is_no_top_level_one(self):
        use: ToolUseBlock = {
            "type": "tool_use",
            "name": "web_search",
            "input": {"_tool_call_id": "toolu_A", "query": "alpha"},
        }
        result: ToolResultBlock = {
            "type": "tool_result",
            "tool_use_id": "toolu_A",
            "content": "alpha hits",
            "is_error": False,
        }
        assert "alpha hits" in extract_text((use, result))

    def it_renders_an_unidentified_batch_unfused(self):
        # captured 2026-06-03: two parallel web_searches whose uses carry
        # `input._tool_call_id` and whose results carry no id at all. The
        # results arrived in completion order -- reversed against call order
        # -- so fusing by position would caption each query with the other's
        # hits. Every block still renders; none is paired.
        uses: list[ToolUseBlock] = [
            {
                "type": "tool_use",
                "name": "web_search",
                "input": {"_tool_call_id": "toolu_A", "query": "alpha"},
            },
            {
                "type": "tool_use",
                "name": "web_search",
                "input": {"_tool_call_id": "toolu_B", "query": "beta"},
            },
        ]
        results: list[ToolResultBlock] = [
            {"type": "tool_result", "name": "web_search", "content": "BBB", "is_error": False},
            {"type": "tool_result", "name": "web_search", "content": "AAA", "is_error": False},
        ]
        text = extract_text((*uses, *results))
        assert text.count('type="tool_call"') == 4
        # both queries render, then both result sets, each in document order --
        # no query sits in a disclosure captioning the other's hits
        assert text.index("alpha") < text.index("beta") < text.index("BBB") < text.index("AAA")

    def it_renders_a_batch_whose_results_never_arrived(self):
        uses: list[ToolUseBlock] = [
            {"type": "tool_use", "name": "web_search", "id": "toolu_A", "input": {"query": "alpha"}},
            {"type": "tool_use", "name": "web_search", "id": "toolu_B", "input": {"query": "beta"}},
        ]
        results: list[ToolResultBlock] = [
            {"type": "tool_result", "tool_use_id": "toolu_A", "content": "alpha hits", "is_error": False},
        ]
        text = extract_text((*uses, *results))
        assert "alpha hits" in text
        assert "beta" in text
        assert text.count('type="tool_call"') == 2

    def it_keeps_two_sequential_calls_fused(self):
        # a run is use-then-result twice over, not a batch: each pair fuses.
        blocks: list[ToolUseBlock | ToolResultBlock] = [
            {"type": "tool_use", "name": "web_search", "input": {"query": "alpha"}},
            {"type": "tool_result", "content": "alpha hits", "is_error": False},
            {"type": "tool_use", "name": "web_search", "input": {"query": "beta"}},
            {"type": "tool_result", "content": "beta hits", "is_error": False},
        ]
        text = extract_text(tuple(blocks))
        assert text.count('type="tool_call"') == 2
        assert "request" not in text
