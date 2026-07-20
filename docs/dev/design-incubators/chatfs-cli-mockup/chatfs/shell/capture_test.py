"""capture()'s outputs go through staged() -- see
.claude/todo.kb/2026-07-13-000-Atomic-chat-dir-regeneration-...md's
"ride-alongs" step. These tests cover the invariant that step exists
for: a failed browse (or pluck) must not destroy a prior capture --
the one artifact class that isn't locally re-derivable."""

from collections.abc import Iterable, Iterator
from pathlib import Path

import pytest

from chatfs import json as chatfs_json
from chatfs.json import JsonValue
from chatfs.layout import chat_dir_for, data_dir_for
from chatfs.shell import capture as chatfs_capture
from chatfs.shell.capture import capture


class DescribeCapture:
    def it_writes_cdp_and_conversation_into_the_data_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        chat_dir = chat_dir_for("abc123", tmp_path)

        def fake_browse(_url: str, dst: Path) -> None:
            _ = dst.write_text('{"line": 1}\n')

        monkeypatch.setattr(chatfs_capture, "browse", fake_browse)

        def pluck_fn(_lines: Iterable[str]) -> Iterator[JsonValue]:
            yield {"ok": True}

        data_dir = capture("https://example/abc123", chat_dir, pluck_fn)

        assert data_dir == data_dir_for("abc123", tmp_path)
        assert (data_dir / "cdp.jsonl").read_text() == '{"line": 1}\n'
        assert chatfs_json.loads((data_dir / "conversation.json").read_text()) == {"ok": True}

    def it_preserves_the_prior_cdp_jsonl_when_browse_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        chat_dir = chat_dir_for("abc123", tmp_path)
        data_dir = data_dir_for("abc123", tmp_path)
        data_dir.mkdir(parents=True)
        _ = (data_dir / "cdp.jsonl").write_text("prior capture")
        _ = (data_dir / "conversation.json").write_text('{"prior": true}')

        def failing_browse(_url: str, dst: Path) -> None:
            _ = dst.write_text("half-written")
            raise RuntimeError("browser crashed")

        monkeypatch.setattr(chatfs_capture, "browse", failing_browse)

        def pluck_fn(_lines: Iterable[str]) -> Iterator[JsonValue]:
            yield {"unreached": True}

        with pytest.raises(RuntimeError):
            _ = capture("https://example/abc123", chat_dir, pluck_fn)

        assert (data_dir / "cdp.jsonl").read_text() == "prior capture"
        assert (data_dir / "conversation.json").read_text() == '{"prior": true}'
        assert (data_dir / ".cdp.jsonl.fail").read_text() == "half-written"

    def it_preserves_the_prior_conversation_when_pluck_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        chat_dir = chat_dir_for("abc123", tmp_path)
        data_dir = data_dir_for("abc123", tmp_path)
        data_dir.mkdir(parents=True)
        _ = (data_dir / "cdp.jsonl").write_text("prior capture")
        _ = (data_dir / "conversation.json").write_text('{"prior": true}')

        def fake_browse(_url: str, dst: Path) -> None:
            _ = dst.write_text("new capture")

        monkeypatch.setattr(chatfs_capture, "browse", fake_browse)

        def failing_pluck_fn(_lines: Iterable[str]) -> Iterator[JsonValue]:
            # raises before yielding anything -- dst.open("w") has already
            # truncated the staged tmp file by the time this runs, so this
            # exercises the "partial output preserved as .fail" path too.
            raise RuntimeError("massage failed")

        with pytest.raises(RuntimeError):
            _ = capture("https://example/abc123", chat_dir, failing_pluck_fn)

        # browse succeeded, so the new cdp.jsonl is kept ...
        assert (data_dir / "cdp.jsonl").read_text() == "new capture"
        # ... but the conversation, which pluck never finished, is untouched
        assert (data_dir / "conversation.json").read_text() == '{"prior": true}'
