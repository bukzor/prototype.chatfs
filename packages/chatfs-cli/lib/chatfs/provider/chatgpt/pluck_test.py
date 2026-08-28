"""Tests for chatfs.provider.chatgpt.pluck's URL patterns -- the wire
knowledge that decides which captured responses carry a conversation.
"""

import json

from . import pluck as M

UUID = "0badc0de-0000-0000-0000-000000000000"
HOST = "https://chatgpt.com"


def response_received(url: str, body: object) -> str:
    return json.dumps(
        {
            "method": "Network.responseReceived",
            "params": {"response": {"url": url, "body": json.dumps(body)}},
        }
    )


def plucked_urls(*urls: str) -> list[str]:
    lines = [response_received(url, {}) for url in urls]
    plucked: list[str] = []
    for record in M.pluck_conversation(lines):
        assert isinstance(record, dict), record
        url = record["url"]
        assert isinstance(url, str), url
        plucked.append(url)
    return plucked


class DescribeConversationUrl:
    def it_matches_a_whole_document_response(self):
        url = f"{HOST}/backend-api/conversation/{UUID}"
        assert plucked_urls(url) == [url]

    def it_matches_the_paginated_conversation_endpoint(self):
        url = f"{HOST}/backend-api/conversations/{UUID}?include_has_versions=true&num_turns=10"
        assert plucked_urls(url) == [url]

    def it_matches_an_older_messages_page(self):
        url = f"{HOST}/backend-api/conversations/{UUID}/messages?before={UUID}&num_turns=10"
        assert plucked_urls(url) == [url]

    def it_skips_sibling_sub_resources(self):
        assert plucked_urls(
            f"{HOST}/backend-api/conversation/{UUID}/textdocs",
            f"{HOST}/backend-api/conversation/{UUID}/stream_status",
            f"{HOST}/backend-api/conversation/init",
        ) == []

    def it_skips_the_index_endpoint(self):
        assert plucked_urls(f"{HOST}/backend-api/conversations?limit=28&offset=0") == []


class DescribeIndexUrl:
    def it_does_not_claim_a_single_conversation(self):
        lines = [response_received(f"{HOST}/backend-api/conversations/{UUID}", {"items": []})]
        assert list(M.pluck_index_pages(lines)) == []

    def it_claims_a_sidebar_page(self):
        lines = [response_received(f"{HOST}/backend-api/conversations?limit=28", {"items": []})]
        assert list(M.pluck_index_pages(lines)) == [{"items": []}]


class DescribePluckConversation:
    def it_tags_each_body_with_its_url(self):
        url = f"{HOST}/backend-api/conversations/{UUID}?num_turns=10"
        lines = [response_received(url, {"conversation_id": UUID})]
        assert list(M.pluck_conversation(lines)) == [
            {"url": url, "body": {"conversation_id": UUID}}
        ]
