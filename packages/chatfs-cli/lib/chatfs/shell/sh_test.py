"""pipe() is the piece a shell `|` does not give you for free: a
non-zero exit *anywhere* in the pipeline is an error, not just the last
stage's. The bare-noun index driver depends on that -- a failed browse
must not be swallowed by a splat that happily reads zero pages."""

import subprocess
import sys
from pathlib import Path

import pytest

from chatfs.shell.sh import pipe


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

        with pytest.raises(subprocess.CalledProcessError) as excinfo:
            pipe(producer, sink(tmp_path / "out"))

        assert excinfo.value.returncode == 3

    def it_raises_when_the_consumer_exits_nonzero(self):
        with pytest.raises(subprocess.CalledProcessError) as excinfo:
            pipe(
                [sys.executable, "-c", "print('page')"],
                [sys.executable, "-c", "raise SystemExit(4)"],
            )

        assert excinfo.value.returncode == 4
