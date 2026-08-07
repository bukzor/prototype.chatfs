"""Regression tests for the AI Studio renderer: the linear (fork-less) chain
this provider's wire shape actually has (see
dev.kb/claims.kb/aistudio-jspb-prompt-shape.md), plus turn loading and the
resulting plain-sequence markdown."""

import json
import time
from pathlib import Path
from textwrap import dedent

import pytest

from chatfs.provider.aistudio.conversation.render import (
    build_tree,
    load_turns,
    parse_stem,
    render_conversation,
)
from chatfs.render import Turn


class DescribeParseStem:
    def it_splits_index_and_role(self):
        assert parse_stem("003.model") == (3, "model", "")

    def it_splits_index_role_and_thought_note(self):
        assert parse_stem("001.model.thought") == (1, "model", "thought")

    def it_rejects_a_malformed_stem(self):
        with pytest.raises(AssertionError):
            _ = parse_stem("weird")


class DescribeLoadTurns:
    def write_turn(
        self,
        tmp_path: Path,
        stem: str,
        *,
        role: str,
        seconds: int,
        body: str | None,
    ) -> None:
        turn = {"role": role, "text": body or "", "createTime": [str(seconds), 0]}
        _ = (tmp_path / f"{stem}.json").write_text(json.dumps(turn) + "\n")
        if body is not None:
            _ = (tmp_path / f"{stem}.md").write_text(body + "\n")

    def it_skips_a_turn_with_no_rendered_body(self, tmp_path: Path):
        # mirrors claude's canceled-retry case: a .json with no .md is not a
        # turn to show, and here (no forking) it just isn't part of the chain
        self.write_turn(tmp_path, "000.user", role="user", seconds=1, body="hi")
        self.write_turn(tmp_path, "001.model", role="model", seconds=2, body=None)
        turns, _ = load_turns(tmp_path)
        assert set(turns) == {"000.user"}

    def it_converts_epoch_seconds_to_local_wall_clock(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setenv("TZ", "America/Chicago")
        time.tzset()
        # matches the observed value from the live demo capture (chatfs.demo)
        self.write_turn(tmp_path, "000.user", role="user", seconds=1781977360, body="hi")
        turns, created = load_turns(tmp_path)
        assert turns["000.user"].time == "2026-06-20T12:42", turns
        assert created["000.user"] == 1781977360

    def it_tags_a_thought_turn_with_a_note_but_not_a_plain_model_turn(
        self, tmp_path: Path
    ):
        self.write_turn(tmp_path, "001.model.thought", role="model", seconds=1, body="thinking")
        self.write_turn(tmp_path, "002.model", role="model", seconds=2, body="answer")
        turns, _ = load_turns(tmp_path)
        assert turns["001.model.thought"].sender == "model"
        assert turns["001.model.thought"].note == "thought"
        assert turns["002.model"].note == ""


class DescribeBuildTree:
    def it_chains_turns_in_the_given_order(self):
        tree = build_tree(["000.user", "001.model"], {"000.user": 1.0, "001.model": 2.0})
        assert tree.parent_of == {"000.user": "", "001.model": "000.user"}
        assert tree.children[""] == ["000.user"]
        assert tree.children["000.user"] == ["001.model"]
        assert tree.children["001.model"] == []
        assert tree.current == "001.model"


class DescribeRenderConversation:
    def it_renders_a_plain_sequence_with_no_fork_facts(self):
        # every node has exactly one child -- chatfs.render's fork machinery
        # (replies/superseded-by/backlinks) must degenerate to nothing.
        turns = {
            "000.user": Turn("user", "T", "L0", "hi"),
            "001.model": Turn("model", "T", "L1", "hello"),
        }
        markdown, count = render_conversation(turns, {"000.user": 1.0, "001.model": 2.0})
        assert count == 2
        assert markdown == dedent("""\
            # [000 · user · T](L0)

            hi

            # [001 · model · T](L1)

            hello
            """)

    def it_orders_by_stem_index_regardless_of_dict_insertion_order(self):
        turns = {
            "001.model": Turn("model", "T", "L1", "hello"),
            "000.user": Turn("user", "T", "L0", "hi"),
        }
        markdown, _ = render_conversation(turns, {"000.user": 1.0, "001.model": 2.0})
        assert markdown.index("hi") < markdown.index("hello")
