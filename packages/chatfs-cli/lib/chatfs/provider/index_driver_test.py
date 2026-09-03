"""Every provider's `index` driver forwards the un-appended `--cache` root
to its two child stages, because each child appends its own provider
segment via extract_cache -- forwarding the driver's already-appended
root would nest the segment twice."""

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

import pytest

import chatfs.provider.aistudio.index.__main__ as aistudio_main
import chatfs.provider.chatgpt.index.__main__ as chatgpt_main
import chatfs.provider.claude.index.__main__ as claude_main
from chatfs.shell import sh as chatfs_sh


class Driver(Protocol):
    def main(self) -> None: ...


DRIVERS: Sequence[tuple[Driver, str]] = (
    (claude_main, "claude"),
    (chatgpt_main, "chatgpt"),
    (aistudio_main, "aistudio"),
)

PipeCall = tuple[Sequence[object], Sequence[object]]


def record_call(calls: list[PipeCall], producer: Sequence[object], consumer: Sequence[object]) -> None:
    calls.append((producer, consumer))


class DescribeIndexDriver:
    @pytest.mark.parametrize("driver, provider", DRIVERS, ids=[p for _, p in DRIVERS])
    def it_forwards_the_cache_root_unappended_to_both_child_stages(
        self,
        driver: Driver,
        provider: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ):
        calls: list[PipeCall] = []
        monkeypatch.setattr(chatfs_sh, "pipe", lambda p, c: record_call(calls, p, c))
        monkeypatch.setattr("sys.argv", ["prog", "--cache", str(tmp_path)])

        driver.main()

        assert len(calls) == 1
        producer, consumer = calls[0]
        for argv in (producer, consumer):
            assert "--cache" in argv
            cache_arg = argv[argv.index("--cache") + 1]
            assert cache_arg == tmp_path
            assert cache_arg != tmp_path / provider
