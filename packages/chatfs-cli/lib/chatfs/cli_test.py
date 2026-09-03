"""Tests for chatfs.cli.extract_cache -- the shared --cache/$CHATFS_CACHE
parsing behind every --cache-taking leaf command."""

from pathlib import Path

import pytest

from chatfs.cli import cache_root, extract_cache


class DescribeExtractCache:
    def it_reads_the_flag_from_the_front(self, tmp_path: Path):
        root, rest = extract_cache(["--cache", str(tmp_path), "url"], {}, "claude")
        assert root == tmp_path / "claude"
        assert rest == ["url"]

    def it_reads_the_flag_after_positional_args(self, tmp_path: Path):
        root, rest = extract_cache(["url", "--cache", str(tmp_path)], {}, "claude")
        assert root == tmp_path / "claude"
        assert rest == ["url"]

    def it_falls_back_to_the_env_var_when_the_flag_is_absent(self, tmp_path: Path):
        root, rest = extract_cache(["url"], {"CHATFS_CACHE": str(tmp_path)}, "claude")
        assert root == tmp_path / "claude"
        assert rest == ["url"]

    def it_prefers_the_flag_over_the_env_var(self, tmp_path: Path):
        explicit = tmp_path / "explicit"
        root, rest = extract_cache(
            ["--cache", str(explicit), "url"],
            {"CHATFS_CACHE": str(tmp_path / "env")},
            "claude",
        )
        assert root == explicit / "claude"
        assert rest == ["url"]

    def it_gives_each_provider_its_own_subtree_of_one_cache(self, tmp_path: Path):
        argv = ["--cache", str(tmp_path)]
        claude, _ = extract_cache(argv, {}, "claude")
        chatgpt, _ = extract_cache(argv, {}, "chatgpt")
        assert (claude, chatgpt) == (tmp_path / "claude", tmp_path / "chatgpt")

    def it_returns_none_when_neither_flag_nor_env_var_is_set(self):
        root, rest = extract_cache(["url"], {}, "claude")
        assert root is None
        assert rest == ["url"]

    def it_drops_a_dangling_flag_with_no_value_and_returns_none(self):
        root, rest = extract_cache(["url", "--cache"], {}, "claude")
        assert root is None
        assert rest == ["url"]

    def it_resolves_a_relative_dir_to_absolute(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.chdir(tmp_path)
        root, _ = extract_cache(["--cache", "."], {}, "claude")
        assert root == tmp_path / "claude"


class DescribeCacheRoot:
    def it_inverts_extract_caches_append(self, tmp_path: Path):
        root, _ = extract_cache(["--cache", str(tmp_path)], {}, "claude")
        assert root is not None
        assert cache_root(root, "claude") == tmp_path

    def it_round_trips_through_extract_cache(self, tmp_path: Path):
        root, _ = extract_cache(["--cache", str(tmp_path)], {}, "claude")
        assert root is not None
        replayed, _ = extract_cache(["--cache", str(cache_root(root, "claude"))], {}, "claude")
        assert replayed == root

    def it_asserts_the_root_ends_in_the_given_provider(self, tmp_path: Path):
        with pytest.raises(AssertionError):
            cache_root(tmp_path / "claude", "chatgpt")
