"""Tests for bukzor.chatgpt_export.har2jsonl."""

import base64
import json
from pathlib import Path

import pytest

from . import har2jsonl as M
from .json import JsonObj, JsonValue


def _har(entries: list[JsonValue]) -> JsonObj:
    return {"log": {"entries": entries}}


def _conversation_entry(
    uuid: str = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    body: JsonObj | None = None,
) -> JsonObj:
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


class DescribeIsConversationEntry:
    def it_matches_conversation_urls(self):
        entry: JsonObj = {
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
            entry: JsonObj = {"request": {"url": url}}
            assert M.is_conversation_entry(entry) is False, url

    def it_handles_missing_request_key(self):
        assert M.is_conversation_entry({}) is False
        assert M.is_conversation_entry({"request": {}}) is False


class DescribeDecodeResponseBody:
    def it_returns_plain_text(self):
        content: JsonObj = {"text": "hello world"}
        assert M.decode_response_body(content) == "hello world"

    def it_decodes_base64_content(self):
        original = '{"title": "Test"}'
        encoded = base64.b64encode(original.encode()).decode()
        content: JsonObj = {"text": encoded, "encoding": "base64"}
        assert M.decode_response_body(content) == original

    def it_returns_empty_string_when_no_text(self):
        assert M.decode_response_body({}) == ""
        assert M.decode_response_body({"encoding": "base64"}) == ""


class DescribeExtractConversations:
    def it_yields_conversation_from_matching_entry(self):
        body: JsonObj = {"title": "My Chat", "mapping": {"root": {}}}
        entry = _conversation_entry(body=body)
        results = list(M.extract_conversations(_har([entry])))
        assert results == [body]

    def it_skips_non_conversation_entries(self):
        entry: JsonObj = {
            "request": {"url": "https://chatgpt.com/backend-api/models"},
            "response": {"content": {"text": "{}"}},
        }
        results = list(M.extract_conversations(_har([entry])))
        assert results == []

    def it_yields_nothing_from_empty_har(self):
        assert list(M.extract_conversations(_har([]))) == []
        assert list(M.extract_conversations({})) == []

    def it_skips_entries_with_empty_body(self):
        entry: JsonObj = {
            "request": {
                "url": "https://chatgpt.com/backend-api/conversation/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
            },
            "response": {"content": {}},
        }
        results = list(M.extract_conversations(_har([entry])))
        assert results == []

    def it_yields_multiple_conversations(self):
        """HAR files can contain multiple conversation fetches."""
        entry1 = _conversation_entry(
            uuid="aaaaaaaa-0000-0000-0000-000000000001",
            body={"title": "Chat 1"},
        )
        entry2 = _conversation_entry(
            uuid="aaaaaaaa-0000-0000-0000-000000000002",
            body={"title": "Chat 2"},
        )
        results = list(M.extract_conversations(_har([entry1, entry2])))
        assert results == [{"title": "Chat 1"}, {"title": "Chat 2"}]


class DescribeMain:
    """Tests for main() JSONL file output."""

    def it_writes_single_conversation_as_jsonl(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ):
        body: JsonObj = {"title": "My Chat", "mapping": {}}
        har = _har([_conversation_entry(body=body)])
        src = tmp_path / "test.har"
        src.write_text(json.dumps(har))

        monkeypatch.setattr("sys.argv", ["har2jsonl", str(src)])
        M.main()

        dest = tmp_path / "test.jsonl"
        lines = dest.read_text().strip().split("\n")
        assert len(lines) == 1
        assert json.loads(lines[0]) == body

    def it_writes_multiple_conversations_as_jsonl(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ):
        entry1 = _conversation_entry(
            uuid="aaaaaaaa-0000-0000-0000-000000000001",
            body={"title": "Chat 1"},
        )
        entry2 = _conversation_entry(
            uuid="aaaaaaaa-0000-0000-0000-000000000002",
            body={"title": "Chat 2"},
        )
        har = _har([entry1, entry2])
        src = tmp_path / "test.har"
        src.write_text(json.dumps(har))

        monkeypatch.setattr("sys.argv", ["har2jsonl", str(src)])
        M.main()

        dest = tmp_path / "test.jsonl"
        lines = dest.read_text().strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0]) == {"title": "Chat 1"}
        assert json.loads(lines[1]) == {"title": "Chat 2"}

    def it_writes_empty_file_when_no_conversations(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ):
        har = _har([])
        src = tmp_path / "test.har"
        src.write_text(json.dumps(har))

        monkeypatch.setattr("sys.argv", ["har2jsonl", str(src)])
        M.main()

        dest = tmp_path / "test.jsonl"
        assert dest.read_text() == ""

    def it_infers_jsonl_extension(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ):
        har = _har([_conversation_entry()])
        src = tmp_path / "export.har"
        src.write_text(json.dumps(har))

        monkeypatch.setattr("sys.argv", ["har2jsonl", str(src)])
        M.main()

        assert (tmp_path / "export.jsonl").exists()
        assert not (tmp_path / "export.json").exists()
