"""The selection rules refresh applies before it spends a click: which
chats are recent, whether the index reached far enough back to say so,
and which of the recent ones the provider changed since we captured."""

import subprocess
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

import pytest

from chatfs.refresh import covers, cutoff_for, day_count, in_window, is_stale, main
from chatfs.shell import sh as chatfs_sh

NOW = datetime(2026, 9, 3, 12, 0, tzinfo=UTC)


class DescribeCutoffFor:
    def it_is_the_window_start(self):
        assert cutoff_for(7, NOW) == NOW - timedelta(days=7)


class DescribeInWindow:
    def it_admits_a_timestamp_inside_the_window(self):
        assert in_window(NOW - timedelta(days=1), cutoff_for(7, NOW))

    def it_rejects_a_timestamp_older_than_the_cutoff(self):
        assert not in_window(NOW - timedelta(days=8), cutoff_for(7, NOW))

    def it_rejects_an_unknown_timestamp(self):
        assert not in_window(None, cutoff_for(7, NOW))


class DescribeCovers:
    def it_is_satisfied_by_one_record_older_than_the_cutoff(self):
        updateds = [NOW - timedelta(days=1), NOW - timedelta(days=9)]
        assert covers(updateds, cutoff_for(7, NOW))

    def it_is_unsatisfied_when_every_record_is_inside_the_window(self):
        updateds = [NOW - timedelta(days=1), NOW - timedelta(days=2)]
        assert not covers(updateds, cutoff_for(7, NOW))

    def it_is_unsatisfied_by_records_with_no_timestamp(self):
        assert not covers([None, None], cutoff_for(7, NOW))


class DescribeIsStale:
    def it_is_stale_when_never_captured(self):
        assert is_stale(NOW - timedelta(days=1), None)

    def it_is_stale_when_captured_before_the_provider_changed_it(self):
        assert is_stale(NOW - timedelta(days=1), NOW - timedelta(days=2))

    def it_is_fresh_when_captured_after_the_provider_changed_it(self):
        assert not is_stale(NOW - timedelta(days=2), NOW - timedelta(days=1))


class DescribeDayCount:
    def it_reads_a_positive_integer(self):
        assert day_count(["7"]) == 7

    def it_rejects_zero(self):
        assert day_count(["0"]) is None

    def it_rejects_a_negative_count(self):
        assert day_count(["-1"]) is None

    def it_rejects_a_non_integer(self):
        assert day_count(["week"]) is None

    def it_rejects_a_missing_argument(self):
        assert day_count([]) is None

    def it_rejects_a_second_argument(self):
        assert day_count(["7", "8"]) is None


class DescribeMain:
    def it_runs_every_provider_even_when_one_fails(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ):
        spawned: list[str] = []

        def fake_run(cmd: Sequence[object], **_kwargs: object) -> None:
            argv = [str(arg) for arg in cmd]
            module = argv[argv.index("-m") + 1]
            spawned.append(module)
            if "chatgpt" in module:
                raise subprocess.CalledProcessError(1, argv)

        monkeypatch.setattr(chatfs_sh, "run", fake_run)
        monkeypatch.setattr("sys.argv", ["prog", "--cache", "/nowhere", "7"])

        with pytest.raises(SystemExit) as exit_info:
            main()

        assert exit_info.value.code == 1
        assert spawned == [
            "chatfs.provider.aistudio.refresh",
            "chatfs.provider.chatgpt.refresh",
            "chatfs.provider.claude.refresh",
        ]
        assert "chatgpt: FAILED" in capsys.readouterr().err
