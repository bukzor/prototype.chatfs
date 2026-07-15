"""Tests for chatfs_layout's shared time_dir_for/place_meta path derivation
— previously untested (see .claude/todo.md's "Next" item), even though the
Created=/LastModified= label switch (2026-07-11) landed with none. Also
covers iter_responses_matching, the skeleton every provider's pluck is
built on (ported 2026-07-14 from six per-provider `.jq` filters)."""

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

import chatfs_json
from chatfs_layout import chat_dir_for, iter_responses_matching, place_meta, time_dir_for

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


# Epoch matches the AI Studio demo capture fixture used elsewhere in this
# incubator; under America/Chicago (CDT, UTC-5) it's 2026-06-20T12:42:40.
DEMO_EPOCH = 1781977360


def use_chicago_tz(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TZ", "America/Chicago")
    time.tzset()


class DescribeTimeDirFor:
    def it_labels_with_created_by_default(self, monkeypatch: pytest.MonkeyPatch):
        use_chicago_tz(monkeypatch)
        dt = datetime.fromtimestamp(DEMO_EPOCH, tz=timezone.utc)
        assert time_dir_for(dt) == Path("Created=2026/06/20/12:42:40-05:00")

    def it_labels_with_a_given_label(self, monkeypatch: pytest.MonkeyPatch):
        use_chicago_tz(monkeypatch)
        dt = datetime.fromtimestamp(DEMO_EPOCH, tz=timezone.utc)
        assert time_dir_for(dt, label="LastModified") == Path(
            "LastModified=2026/06/20/12:42:40-05:00"
        )


class DescribePlaceMeta:
    def it_writes_meta_json_and_a_view_symlink(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        use_chicago_tz(monkeypatch)
        dt = datetime.fromtimestamp(DEMO_EPOCH, tz=timezone.utc)
        chat_dir = place_meta("abc123", "Hello", dt, {"foo": "bar"}, tmp_path)

        assert chat_dir == chat_dir_for("abc123", tmp_path)
        meta = chatfs_json.loads((chat_dir / ".data" / "meta.json").read_text())
        assert meta == {"foo": "bar"}

        link = tmp_path / "Created=2026/06/20/12:42:40-05:00" / "Hello"
        assert link.is_symlink()
        assert link.resolve() == chat_dir.resolve()

    def it_moves_the_symlink_when_a_later_call_uses_a_different_label(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        # mirrors the real sequence: an index-only sighting places a
        # LastModified= symlink first; a later, richer sighting (real
        # create_time) replaces it under Created= — see no-partial-synthesis.md
        use_chicago_tz(monkeypatch)
        dt = datetime.fromtimestamp(DEMO_EPOCH, tz=timezone.utc)
        _ = place_meta(
            "abc123", "Hello", dt, {"stub": True}, tmp_path, label="LastModified"
        )
        stale_link = tmp_path / "LastModified=2026/06/20/12:42:40-05:00" / "Hello"
        assert stale_link.is_symlink()

        chat_dir = place_meta("abc123", "Hello", dt, {"real": True}, tmp_path)

        assert not stale_link.is_symlink()
        fresh_link = tmp_path / "Created=2026/06/20/12:42:40-05:00" / "Hello"
        assert fresh_link.is_symlink()
        assert fresh_link.resolve() == chat_dir.resolve()
        meta = chatfs_json.loads((chat_dir / ".data" / "meta.json").read_text())
        assert meta == {"real": True}
