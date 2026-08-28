"""Tests for the provider-dispatching commands' one job: naming the provider
a locator belongs to."""

from pathlib import Path
from urllib.parse import urlparse

import pytest

from chatfs.conversation.dispatch import (
    provider_for_path,
    provider_for_url,
    url_in,
)
from chatfs.provider.aistudio import layout as aistudio_layout
from chatfs.provider.chatgpt import layout as chatgpt_layout
from chatfs.provider.claude import layout as claude_layout
from chatfs.provider.registry import PROVIDERS, PROVIDER_BY_HOST


class DescribeProviderForUrl:
    @pytest.mark.parametrize(
        ("url", "provider"),
        [
            ("https://claude.ai/chat/abc-123", "claude"),
            ("https://chatgpt.com/c/abc-123", "chatgpt"),
            ("https://aistudio.google.com/prompts/abc-123", "aistudio"),
        ],
    )
    def it_reads_the_provider_off_the_host(self, url: str, provider: str):
        assert provider_for_url(url) == provider

    def it_names_the_known_hosts_when_it_does_not_recognise_one(self):
        with pytest.raises(AssertionError) as caught:
            _ = provider_for_url("https://gemini.google.com/app/abc-123")
        assert "gemini.google.com" in str(caught.value)

    def it_ignores_the_path_which_differs_per_provider(self):
        assert provider_for_url("https://claude.ai/anything/at/all") == "claude"


class DescribeUrlIn:
    def it_finds_the_url_among_flags(self):
        argv = ["--cache", "/tmp/c", "https://claude.ai/chat/x"]
        assert url_in(argv) == "https://claude.ai/chat/x"

    def it_finds_the_url_before_flags(self):
        argv = ["https://chatgpt.com/c/x", "--cache", "/tmp/c"]
        assert url_in(argv) == "https://chatgpt.com/c/x"

    def it_returns_none_when_no_argument_carries_a_scheme(self):
        assert url_in(["--cache", "/tmp/c"]) is None


class DescribeRegistry:
    def it_maps_every_host_to_a_known_provider(self):
        assert set(PROVIDER_BY_HOST.values()) == PROVIDERS

    def it_keeps_one_host_per_provider(self):
        assert len(PROVIDER_BY_HOST) == len(PROVIDERS)

    def it_routes_each_layout_s_own_url_for_back_to_that_layout(self):
        """The registry and `url_for` must not drift: a link this codebase
        builds has to dispatch back to the provider that built it."""
        built = (
            urlparse(aistudio_layout.url_for("some-id")).netloc,
            urlparse(chatgpt_layout.url_for("some-id")).netloc,
            urlparse(claude_layout.url_for("some-id")).netloc,
        )
        assert tuple(PROVIDER_BY_HOST[host] for host in built) == (
            aistudio_layout.PROVIDER,
            chatgpt_layout.PROVIDER,
            claude_layout.PROVIDER,
        )


UUID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


class DescribeProviderForPath:
    """The provider is a path segment the cache root already carries, so it is
    read rather than guessed. Every address `resolve_chat_dir` accepts has to
    land on the same answer."""

    def it_reads_the_segment_from_a_chat_dir(self, tmp_path: Path):
        assert provider_for_path(str(tmp_path / "claude/.chat" / UUID)) == "claude"

    def it_reads_the_segment_from_a_path_inside_a_chat_dir(self, tmp_path: Path):
        inside = tmp_path / "chatgpt/.chat" / UUID / "messages/001.md"
        assert provider_for_path(str(inside)) == "chatgpt"

    def it_reads_the_segment_from_the_data_twin(self, tmp_path: Path):
        assert provider_for_path(str(tmp_path / "aistudio/.data" / UUID)) == "aistudio"

    def it_follows_a_view_symlink_to_its_provider(self, tmp_path: Path):
        chat_dir = tmp_path / "claude/.chat" / UUID
        chat_dir.mkdir(parents=True)
        view = tmp_path / "claude/Created=2026/01/02"
        view.mkdir(parents=True)
        link = view / "Some Title"
        link.symlink_to(chat_dir)
        assert provider_for_path(str(link)) == "claude"

    def it_rejects_a_segment_that_names_no_provider(self, tmp_path: Path):
        with pytest.raises(AssertionError) as caught:
            _ = provider_for_path(str(tmp_path / "gemini/.chat" / UUID))
        assert "gemini" in str(caught.value)
