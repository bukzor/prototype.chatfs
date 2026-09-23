"""pipe() is the piece a shell `|` does not give you for free: a
non-zero exit *anywhere* in the pipeline is an error, not just the last
stage's. The bare-noun index driver depends on that -- a failed browse
must not be swallowed by a splat that happily reads zero pages."""

import sys
from pathlib import Path

import pytest

from chatfs.shell.sh import pipe, run
from chatfs.user_error import UserError


def sink(dst: Path) -> list[str]:
    """A consumer command that copies its stdin to dst."""
    return [
        sys.executable,
        "-c",
        "import pathlib, sys; pathlib.Path(sys.argv[1]).write_text(sys.stdin.read())",
        str(dst),
    ]


class DescribePipe:
    def it_streams_producer_stdout_into_consumer_stdin(self, tmp_path: Path):
        out = tmp_path / "out"

        pipe([sys.executable, "-c", "print('page')"], sink(out))

        assert out.read_text() == "page\n"

    def it_raises_when_the_producer_exits_nonzero(self, tmp_path: Path):
        producer = [sys.executable, "-c", "print('partial'); raise SystemExit(3)"]

        with pytest.raises(UserError) as excinfo:
            pipe(producer, sink(tmp_path / "out"))

        assert excinfo.value.status == 3

    def it_raises_when_the_consumer_exits_nonzero(self):
        with pytest.raises(UserError) as excinfo:
            pipe(
                [sys.executable, "-c", "print('page')"],
                [sys.executable, "-c", "raise SystemExit(4)"],
            )

        assert excinfo.value.status == 4


class DescribeRun:
    def it_raises_a_message_less_user_error_with_the_child_status(self):
        with pytest.raises(UserError) as excinfo:
            _ = run([sys.executable, "-c", "raise SystemExit(5)"])

        assert (str(excinfo.value), excinfo.value.status) == ("", 5)

    def it_reports_a_signal_death_as_the_shell_does(self):
        with pytest.raises(UserError) as excinfo:
            _ = run([sys.executable, "-c", "import os; os.kill(os.getpid(), 15)"])

        assert excinfo.value.status == 128 + 15
