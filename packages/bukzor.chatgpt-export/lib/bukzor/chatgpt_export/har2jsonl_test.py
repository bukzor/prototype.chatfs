"""Tests for bukzor.chatgpt_export.har2jsonl."""

import base64
import json

from . import har2jsonl as M


class DescribeIsConversationEntry:
    def it_matches_conversation_urls(self):
        entry = {
            "request": {
                "url": "https://chatgpt.com/backend-api/conversation/abc12345-def6-7890-abcd-ef1234567890"
            }
        }
        assert M.is_conversation_entry(entry) is True

    def it_rejects_non_conversation_urls(self):
        for url in [
            "https://chatgpt.com/backend-api/conversations",
            "https://chatgpt.com/backend-api/models",
            "https://chatgpt.com/backend-api/conversation",  # no UUID
        ]:
            entry = {"request": {"url": url}}
            assert M.is_conversation_entry(entry) is False, url

    def it_handles_missing_request_key(self):
        assert M.is_conversation_entry({}) is False
        assert M.is_conversation_entry({"request": {}}) is False


class DescribeDecodeResponseBody:
    def it_returns_plain_text(self):
        content = {"text": "hello world"}
        assert M.decode_response_body(content) == "hello world"

    def it_decodes_base64_content(self):
        original = '{"title": "Test"}'
        encoded = base64.b64encode(original.encode()).decode()
        content = {"text": encoded, "encoding": "base64"}
        assert M.decode_response_body(content) == original

    def it_returns_empty_string_when_no_text(self):
        assert M.decode_response_body({}) == ""
        assert M.decode_response_body({"encoding": "base64"}) == ""


class DescribeExtractConversations:
    def _har(self, entries):
        return {"log": {"entries": entries}}

    def _conversation_entry(self, uuid="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", body=None):
        if body is None:
            body = {"title": "Test Chat", "mapping": {}}
        return {
            "request": {
                "url": f"https://chatgpt.com/backend-api/conversation/{uuid}"
            },
            "response": {
                "content": {"text": json.dumps(body)}
            },
        }

    def it_yields_conversation_from_matching_entry(self):
        body = {"title": "My Chat", "mapping": {"root": {}}}
        entry = self._conversation_entry(body=body)
        results = list(M.extract_conversations(self._har([entry])))
        assert results == [body]

    def it_skips_non_conversation_entries(self):
        entry = {
            "request": {"url": "https://chatgpt.com/backend-api/models"},
            "response": {"content": {"text": "{}"}},
        }
        results = list(M.extract_conversations(self._har([entry])))
        assert results == []

    def it_yields_nothing_from_empty_har(self):
        assert list(M.extract_conversations(self._har([]))) == []
        assert list(M.extract_conversations({})) == []

    def it_skips_entries_with_empty_body(self):
        entry = {
            "request": {
                "url": "https://chatgpt.com/backend-api/conversation/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
            },
            "response": {"content": {}},
        }
        results = list(M.extract_conversations(self._har([entry])))
        assert results == []
