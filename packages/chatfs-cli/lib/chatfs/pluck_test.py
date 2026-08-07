"""Tests for chatfs.pluck.iter_responses_matching, the skeleton every
provider's pluck is built on (ported 2026-07-14 from six per-provider
`.jq` filters)."""

import json
import re

from chatfs.pluck import iter_responses_matching

# Shapes below are modeled on real captures inspected during the 2026-07-14
# jq/sh port (a live `aistudio.cdp.jsonl`/`chatgpt.2.cdp.jsonl` capture):
# a `Network.responseReceived` event's body lives at `params.response.body`
# as a JSON-encoded string; preflight/204/interrupted responses carry a
# `null` body instead of a string.
CHATGPT_CONVERSATION_URL = re.compile(r"/backend-api/conversation/[0-9a-f-]+$")


def response_received(url: str, body: object | None) -> str:
    return json.dumps(
        {
            "method": "Network.responseReceived",
            "params": {"response": {"url": url, "body": body}},
        }
    )


class DescribeIterResponsesMatching:
    def it_yields_the_parsed_body_of_a_matching_response(self):
        lines = [
            response_received(
                "https://chatgpt.com/backend-api/conversation/0badc0de-0000-0000-0000-000000000000",
                json.dumps({"conversation_id": "0badc0de"}),
            )
        ]
        assert list(iter_responses_matching(lines, CHATGPT_CONVERSATION_URL)) == [
            {"conversation_id": "0badc0de"}
        ]

    def it_skips_a_url_that_does_not_match(self):
        lines = [
            response_received(
                "https://chatgpt.com/backend-api/conversations?limit=28",
                json.dumps({"items": []}),
            )
        ]
        assert list(iter_responses_matching(lines, CHATGPT_CONVERSATION_URL)) == []

    def it_skips_a_non_response_received_event(self):
        line = json.dumps(
            {
                "method": "Network.requestWillBeSent",
                "params": {
                    "request": {
                        "url": "https://chatgpt.com/backend-api/conversation/0badc0de"
                    }
                },
            }
        )
        assert list(iter_responses_matching([line], CHATGPT_CONVERSATION_URL)) == []

    def it_skips_a_non_string_body(self):
        # a 204 or interrupted response: real captures carry `body: null`
        # here, never an empty string.
        lines = [
            response_received(
                "https://chatgpt.com/backend-api/conversation/0badc0de", None
            )
        ]
        assert list(iter_responses_matching(lines, CHATGPT_CONVERSATION_URL)) == []

    def it_skips_blank_lines(self):
        lines = ["", "   \n"]
        assert list(iter_responses_matching(lines, CHATGPT_CONVERSATION_URL)) == []

    def it_yields_once_per_matching_event_across_multiple_lines(self):
        lines = [
            response_received(
                "https://chatgpt.com/backend-api/conversation/aaaaaaaa",
                json.dumps({"conversation_id": "aaaaaaaa"}),
            ),
            response_received(
                "https://chatgpt.com/backend-api/conversation/bbbbbbbb",
                json.dumps({"conversation_id": "bbbbbbbb"}),
            ),
        ]
        assert list(iter_responses_matching(lines, CHATGPT_CONVERSATION_URL)) == [
            {"conversation_id": "aaaaaaaa"},
            {"conversation_id": "bbbbbbbb"},
        ]
