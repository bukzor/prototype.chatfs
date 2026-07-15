"""Tests for chatfs_aistudio_layout's pluck_conversation/pluck_index_pages —
the two provider plucks with real logic beyond iter_responses_matching's
shared skeleton (guard + flatten), ported 2026-07-14 from
chatfs_aistudio_conversation_pluck.jq / chatfs_aistudio_index_pluck.jq.

Envelope shapes are trimmed synthetic versions of what a real
ResolveDriveResource/ListPrompts capture holds (verified during the port
against a live `aistudio.cdp.jsonl`): a JSPB positional array, not a keyed
object."""

import json

from chatfs_aistudio_layout import pluck_conversation, pluck_index_pages

CONVERSATION_URL = (
    "https://alkalimakersuite-pa.clients6.google.com/$rpc/google.internal"
    ".alkali.applications.makersuite.v1.MakerSuiteService/ResolveDriveResource"
)
INDEX_URL = (
    "https://alkalimakersuite-pa.clients6.google.com/$rpc/google.internal"
    ".alkali.applications.makersuite.v1.MakerSuiteService/ListPrompts"
)


def response_received(url: str, body: object) -> str:
    return json.dumps(
        {
            "method": "Network.responseReceived",
            "params": {"response": {"url": url, "body": json.dumps(body)}},
        }
    )


class DescribePluckConversation:
    def it_yields_each_message_in_a_prompt_envelope(self):
        envelope = [["prompts/abc123", None, None, [1]]]
        lines = [response_received(CONVERSATION_URL, envelope)]
        assert list(pluck_conversation(lines)) == envelope

    def it_skips_a_non_prompt_drive_resource(self):
        # ResolveDriveResource resolves any Drive resource, not just
        # prompts — a non-prompt hit must not be mistaken for one.
        envelope = [["files/some-other-resource", None]]
        lines = [response_received(CONVERSATION_URL, envelope)]
        assert list(pluck_conversation(lines)) == []

    def it_skips_an_empty_envelope(self):
        lines = [response_received(CONVERSATION_URL, [])]
        assert list(pluck_conversation(lines)) == []


class DescribePluckIndexPages:
    def it_flattens_the_entry_list(self):
        entries = [["prompts/a"], ["prompts/b"]]
        lines = [response_received(INDEX_URL, [entries])]
        assert list(pluck_index_pages(lines)) == entries

    def it_yields_nothing_for_an_empty_page(self):
        no_entries: list[object] = []
        lines = [response_received(INDEX_URL, [no_entries])]
        assert list(pluck_index_pages(lines)) == []
