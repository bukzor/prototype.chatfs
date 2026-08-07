"""Regression tests for splat's content-block extraction."""

import pytest

from chatfs.provider.claude.conversation.splat import extract_text
from chatfs.provider.claude.types import ToolUseBlock


class DescribeExtractText:
    def it_rejects_a_trailing_unpaired_tool_use(self):
        # an interrupted tool call: tool_use is the final block, no result ever
        # arrived -- must fail with the mispairing message, not an IndexError.
        block: ToolUseBlock = {
            "type": "tool_use",
            "id": "t1",
            "name": "web_search",
            "input": {"query": "x"},
            "message": "",
        }
        with pytest.raises(
            AssertionError, match="tool_use without following tool_result"
        ):
            _ = extract_text((block,))
