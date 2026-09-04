"""Every command that spawns a `--cache` child forwards the un-appended
cache root, because each child appends its own provider segment via
extract_cache -- forwarding the spawner's already-appended provider root
would nest the segment twice."""

import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

import pytest

import chatfs.provider.aistudio.index.__main__ as aistudio_index
import chatfs.provider.aistudio.refresh as aistudio_refresh
import chatfs.provider.chatgpt.index.__main__ as chatgpt_index
import chatfs.provider.chatgpt.refresh as chatgpt_refresh
import chatfs.provider.claude.index.__main__ as claude_index
import chatfs.provider.claude.refresh as claude_refresh
from chatfs.shell import sh as chatfs_sh


class Command(Protocol):
    def main(self) -> None: ...


INDEX_DRIVERS: Sequence[tuple[Command, str]] = (
    (claude_index, "claude"),
    (chatgpt_index, "chatgpt"),
    (aistudio_index, "aistudio"),
)

REFRESH_LEAVES: Sequence[tuple[Command, str]] = (
    (claude_refresh, "claude"),
    (chatgpt_refresh, "chatgpt"),
    (aistudio_refresh, "aistudio"),
)

PROVIDERS = [provider for _, provider in INDEX_DRIVERS]


def cache_arg(argv: Sequence[object]) -> object:
    assert "--cache" in argv, argv
    return argv[argv.index("--cache") + 1]


class DescribeIndexDriver:
    @pytest.mark.parametrize("driver, provider", INDEX_DRIVERS, ids=PROVIDERS)
    def it_forwards_the_cache_root_unappended_to_both_child_stages(
        self,
        driver: Command,
        provider: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ):
        calls: list[tuple[Sequence[object], Sequence[object]]] = []

        def record(producer: Sequence[object], consumer: Sequence[object]):
            calls.append((producer, consumer))

        monkeypatch.setattr(chatfs_sh, "pipe", record)
        monkeypatch.setattr("sys.argv", ["prog", "--cache", str(tmp_path)])

        driver.main()

        assert len(calls) == 1
        for argv in calls[0]:
            assert cache_arg(argv) == tmp_path
            assert cache_arg(argv) != tmp_path / provider


class DescribeRefreshLeaf:
    @pytest.mark.parametrize("leaf, provider", REFRESH_LEAVES, ids=PROVIDERS)
    def it_forwards_the_cache_root_unappended_to_the_index_child(
        self,
        leaf: Command,
        provider: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ):
        calls: list[Sequence[object]] = []

        def record(cmd: Sequence[object], **_: object):
            calls.append(cmd)
            return subprocess.CompletedProcess(["python"], 0, stdout=b"")

        monkeypatch.setattr(chatfs_sh, "run", record)
        monkeypatch.setattr("sys.argv", ["prog", "--cache", str(tmp_path), "1"])

        # An empty index covers nothing, so the leaf exits 3 before browsing
        # -- the one spawn it did make is what this is about.
        with pytest.raises(SystemExit):
            leaf.main()

        assert len(calls) == 1
        assert cache_arg(calls[0]) == tmp_path
        assert cache_arg(calls[0]) != tmp_path / provider
