"""Tests for chatfs_layout's shared time_dir_for/place_meta path derivation
— previously untested (see .claude/todo.md's "Next" item), even though the
Created=/LastModified= label switch (2026-07-11) landed with none."""

import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

import chatfs_json
from chatfs_layout import chat_dir_for, place_meta, time_dir_for

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
