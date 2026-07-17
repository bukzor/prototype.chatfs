"""Tests for chatfs_layout's shared time_dir_for/place_meta path derivation
— previously untested (see .claude/todo.md's "Next" item), even though the
Created=/LastModified= label switch (2026-07-11) landed with none."""

import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

import chatfs_json
from chatfs_layout import (
    chat_dir_for,
    data_dir_for,
    data_dir_of,
    link_data_dir,
    place_meta,
    resolve_chat_dir,
    time_dir_for,
)

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
        assert not chat_dir.exists()  # place_meta doesn't touch .chat/ -- render's job
        meta = chatfs_json.loads((data_dir_for("abc123", tmp_path) / "meta.json").read_text())
        assert meta == {"foo": "bar"}

        link = tmp_path / "Created=2026/06/20/12:42:40-05:00" / "Hello"
        assert link.is_symlink()
        assert link.resolve() == chat_dir.resolve()  # dangling: resolves, doesn't exist

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
        meta = chatfs_json.loads((data_dir_for("abc123", tmp_path) / "meta.json").read_text())
        assert meta == {"real": True}

    def it_does_not_purge_a_rendered_chats_data_inspection_symlink(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        # regression: _purge_view_symlinks used to sweep by "target string
        # contains uuid", which also matched .chat/$UUID/.data's inspection
        # link (target ../../.data/$UUID) -- a re-place_meta after a render
        # must not delete it.
        use_chicago_tz(monkeypatch)
        dt = datetime.fromtimestamp(DEMO_EPOCH, tz=timezone.utc)
        chat_dir = place_meta("abc123", "Hello", dt, {"v": 1}, tmp_path)
        chat_dir.mkdir(parents=True)
        link_data_dir(chat_dir, "abc123")

        _ = place_meta("abc123", "Hello", dt, {"v": 2}, tmp_path)

        data_link = chat_dir / ".data"
        assert data_link.is_symlink()
        assert data_link.resolve() == data_dir_for("abc123", tmp_path).resolve()


class DescribeDataDirOf:
    def it_derives_the_data_dir_from_a_chat_dir(self, tmp_path: Path):
        chat_dir = chat_dir_for("abc123", tmp_path)
        assert data_dir_of(chat_dir) == data_dir_for("abc123", tmp_path)


class DescribeLinkDataDir:
    def it_links_to_the_data_dir_from_the_final_chat_dir(self, tmp_path: Path):
        chat_dir = chat_dir_for("abc123", tmp_path)
        chat_dir.mkdir(parents=True)
        data_dir_for("abc123", tmp_path).mkdir(parents=True)

        link_data_dir(chat_dir, "abc123")

        data_link = chat_dir / ".data"
        assert data_link.is_symlink()
        assert data_link.resolve() == data_dir_for("abc123", tmp_path).resolve()

    def it_uses_the_same_relative_target_from_a_staged_scratch_sibling(
        self, tmp_path: Path
    ):
        # same-depth sibling of the real chat_dir (root/.chat/.{uuid}.tmp/),
        # per chatfs_atomic's sibling-naming convention
        scratch = tmp_path / ".chat" / ".abc123.tmp"
        scratch.mkdir(parents=True)
        data_dir_for("abc123", tmp_path).mkdir(parents=True)

        link_data_dir(scratch, "abc123")

        data_link = scratch / ".data"
        assert data_link.is_symlink()
        assert data_link.resolve() == data_dir_for("abc123", tmp_path).resolve()

    def it_replaces_a_prior_link(self, tmp_path: Path):
        chat_dir = chat_dir_for("abc123", tmp_path)
        chat_dir.mkdir(parents=True)
        (chat_dir / ".data").symlink_to("stale-target")

        link_data_dir(chat_dir, "abc123")

        assert (chat_dir / ".data").resolve() == data_dir_for("abc123", tmp_path).resolve()


class DescribeResolveChatDir:
    def it_resolves_the_chat_dir_itself_even_when_nonexistent(self, tmp_path: Path):
        chat_dir = chat_dir_for("abc123", tmp_path)
        assert not chat_dir.exists()
        assert resolve_chat_dir(chat_dir) == chat_dir

    def it_resolves_a_file_inside_an_existing_chat_dir(self, tmp_path: Path):
        chat_dir = chat_dir_for("abc123", tmp_path)
        chat_dir.mkdir(parents=True)
        _ = (chat_dir / "chat.md").write_text("hi")

        assert resolve_chat_dir(chat_dir / "chat.md") == chat_dir

    def it_resolves_through_an_existing_view_symlink(self, tmp_path: Path):
        chat_dir = chat_dir_for("abc123", tmp_path)
        chat_dir.mkdir(parents=True)
        view_dir = tmp_path / "Created=2026" / "06" / "20"
        view_dir.mkdir(parents=True)
        view_link = view_dir / "Hello"
        view_link.symlink_to(os.path.relpath(chat_dir, start=view_dir))

        assert resolve_chat_dir(view_link).resolve() == chat_dir.resolve()

    def it_resolves_through_a_dangling_view_symlink(self, tmp_path: Path):
        chat_dir = chat_dir_for("abc123", tmp_path)  # never created
        view_dir = tmp_path / "Created=2026" / "06" / "20"
        view_dir.mkdir(parents=True)
        view_link = view_dir / "Hello"
        view_link.symlink_to(os.path.relpath(chat_dir, start=view_dir))

        assert resolve_chat_dir(view_link) == chat_dir.resolve()

    def it_resolves_a_path_inside_data_dir_directly(self, tmp_path: Path):
        data_dir = data_dir_for("abc123", tmp_path)
        data_dir.mkdir(parents=True)
        _ = (data_dir / "meta.json").write_text("{}")

        assert resolve_chat_dir(data_dir / "meta.json") == chat_dir_for("abc123", tmp_path)

    def it_resolves_through_the_chat_dirs_own_data_inspection_symlink(self, tmp_path: Path):
        chat_dir = chat_dir_for("abc123", tmp_path)
        chat_dir.mkdir(parents=True)
        data_dir_for("abc123", tmp_path).mkdir(parents=True)
        link_data_dir(chat_dir, "abc123")

        resolved = resolve_chat_dir(chat_dir / ".data" / "meta.json")
        assert resolved == chat_dir

    def it_raises_on_input_with_no_chat_or_data_ancestor(self, tmp_path: Path):
        stray = tmp_path / "unrelated" / "file.txt"
        stray.parent.mkdir(parents=True)
        _ = stray.write_text("x")
        with pytest.raises(AssertionError, match="reached fs root"):
            _ = resolve_chat_dir(stray)
