"""Tests for chatfs.cli.extract_cache -- the shared --cache/$CHATFS_CACHE
parsing behind every --cache-taking leaf command."""

from pathlib import Path

import pytest

from chatfs.cli import extract_cache


class DescribeExtractCache:
    def it_reads_the_flag_from_the_front(self, tmp_path: Path):
        root, rest = extract_cache(["--cache", str(tmp_path), "url"], {})
        assert root == tmp_path
        assert rest == ["url"]

    def it_reads_the_flag_after_positional_args(self, tmp_path: Path):
        root, rest = extract_cache(["url", "--cache", str(tmp_path)], {})
        assert root == tmp_path
        assert rest == ["url"]

    def it_falls_back_to_the_env_var_when_the_flag_is_absent(self, tmp_path: Path):
        root, rest = extract_cache(["url"], {"CHATFS_CACHE": str(tmp_path)})
        assert root == tmp_path
        assert rest == ["url"]

    def it_prefers_the_flag_over_the_env_var(self, tmp_path: Path):
        explicit = tmp_path / "explicit"
        root, rest = extract_cache(
            ["--cache", str(explicit), "url"], {"CHATFS_CACHE": str(tmp_path / "env")}
        )
        assert root == explicit
        assert rest == ["url"]

    def it_returns_none_when_neither_flag_nor_env_var_is_set(self):
        root, rest = extract_cache(["url"], {})
        assert root is None
        assert rest == ["url"]

    def it_drops_a_dangling_flag_with_no_value_and_returns_none(self):
        root, rest = extract_cache(["url", "--cache"], {})
        assert root is None
        assert rest == ["url"]

    def it_resolves_a_relative_dir_to_absolute(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.chdir(tmp_path)
        root, _ = extract_cache(["--cache", "."], {})
        assert root == tmp_path
