"""What a refresh run does to a captured index, without a browser.

`sh.run` is the whole boundary: stubbing it serves a canned index on the
driver's stdin-equivalent and records the browses it would have opened,
so every decision the driver makes is observable offline.
"""

import json
import subprocess
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import IO

import pytest

from chatfs.layout import chat_dir_for, data_dir_for
from chatfs.shell import sh as chatfs_sh
from chatfs.shell.refresh import refresh_provider

NOW = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)
DAYS = 7


def days_ago(n: float) -> datetime:
    return NOW - timedelta(days=n)


def make_chat(
    root: Path, uuid: str, updated: datetime | None, captured: datetime | None
) -> dict[str, str | None]:
    """Place one chat's captured state, and return the index record that
    would name it."""
    if captured is not None:
        data_dir = data_dir_for(uuid, root)
        data_dir.mkdir(parents=True)
        conversation = data_dir / "conversation.json"
        _ = conversation.write_text("{}")
        import os

        os.utime(conversation, (captured.timestamp(), captured.timestamp()))
    return {
        "id": uuid,
        "title": uuid,
        "chat_dir": str(chat_dir_for(uuid, root)),
        "view": str(root / "view" / uuid),
        "updated": updated.isoformat() if updated else None,
    }


class FakeRun:
    """Stands in for `sh.run`: answers the index call from a canned
    stream, records every browse, and fails the ones named."""

    def __init__(
        self, index: Iterable[dict[str, str | None]], failing: Iterable[str] = ()
    ) -> None:
        self.index: bytes = "".join(json.dumps(r) + "\n" for r in index).encode()
        self.failing: frozenset[str] = frozenset(failing)
        self.browsed: list[str] = []

    def __call__(
        self,
        cmd: Sequence[object],
        *,
        stdin: IO[bytes] | int | None = None,
        stdout: IO[bytes] | int | None = None,
        timeout: float | None = None,
    ) -> subprocess.CompletedProcess[bytes]:
        argv = [str(arg) for arg in cmd]
        module = argv[argv.index("-m") + 1]
        if module.endswith(".index"):
            return subprocess.CompletedProcess(argv, 0, self.index)
        assert module.endswith(".conversation.path_browse"), argv
        target = argv[-1]
        self.browsed.append(target)
        if target in self.failing:
            raise subprocess.CalledProcessError(1, argv)
        return subprocess.CompletedProcess(argv, 0, b"")


class DescribeRefreshProvider:
    def it_browses_a_chat_the_provider_changed_since_the_capture(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ):
        stale = make_chat(tmp_path, "stale", days_ago(1), days_ago(2))
        anchor = make_chat(tmp_path, "anchor", days_ago(30), days_ago(30))
        fake = FakeRun([stale, anchor])
        monkeypatch.setattr(chatfs_sh, "run", fake)

        status = refresh_provider("claude", tmp_path, DAYS, NOW)

        assert status == 0
        assert fake.browsed == [stale["chat_dir"]]
        out = capsys.readouterr().out.splitlines()
        assert [json.loads(line) for line in out] == [stale]

    def it_leaves_a_chat_captured_after_its_last_change_alone(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        fresh = make_chat(tmp_path, "fresh", days_ago(2), days_ago(1))
        anchor = make_chat(tmp_path, "anchor", days_ago(30), days_ago(30))
        fake = FakeRun([fresh, anchor])
        monkeypatch.setattr(chatfs_sh, "run", fake)

        assert refresh_provider("claude", tmp_path, DAYS, NOW) == 0
        assert fake.browsed == []

    def it_leaves_a_chat_older_than_the_window_alone(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        old = make_chat(tmp_path, "old", days_ago(30), None)
        recent = make_chat(tmp_path, "recent", days_ago(1), days_ago(1))
        fake = FakeRun([old, recent])
        monkeypatch.setattr(chatfs_sh, "run", fake)

        assert refresh_provider("claude", tmp_path, DAYS, NOW) == 0
        assert fake.browsed == []

    def it_reports_records_carrying_no_timestamp(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ):
        undated = make_chat(tmp_path, "undated", None, None)
        anchor = make_chat(tmp_path, "anchor", days_ago(30), days_ago(30))
        fake = FakeRun([undated, anchor])
        monkeypatch.setattr(chatfs_sh, "run", fake)

        assert refresh_provider("claude", tmp_path, DAYS, NOW) == 0
        assert fake.browsed == []
        assert "1 record(s) carried no timestamp" in capsys.readouterr().err

    class WhenTheIndexStopsShortOfTheWindow:
        def it_fails_before_browsing_anything(
            self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
        ):
            stale = make_chat(tmp_path, "stale", days_ago(1), days_ago(2))
            also_stale = make_chat(tmp_path, "also-stale", days_ago(3), None)
            fake = FakeRun([stale, also_stale])
            monkeypatch.setattr(chatfs_sh, "run", fake)

            status = refresh_provider("claude", tmp_path, DAYS, NOW)

            assert status == 3
            assert fake.browsed == []
            assert "2026-08-27" in capsys.readouterr().err

    class WhenOneBrowseFails:
        def it_still_browses_the_rest(
            self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
        ):
            doomed = make_chat(tmp_path, "doomed", days_ago(1), None)
            ok = make_chat(tmp_path, "ok", days_ago(1), None)
            anchor = make_chat(tmp_path, "anchor", days_ago(30), days_ago(30))
            fake = FakeRun([doomed, ok, anchor], failing=[str(doomed["chat_dir"])])
            monkeypatch.setattr(chatfs_sh, "run", fake)

            status = refresh_provider("claude", tmp_path, DAYS, NOW)

            assert status == 1
            assert fake.browsed == [doomed["chat_dir"], ok["chat_dir"]]
            captured = capsys.readouterr()
            assert str(doomed["chat_dir"]) in captured.err
            assert [json.loads(line) for line in captured.out.splitlines()] == [ok]
