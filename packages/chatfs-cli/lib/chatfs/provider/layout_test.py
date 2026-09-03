"""The provider adapters' shared surface: the PROVIDER path segment and
`updated_at`, each provider's own answer to "when did this chat last
change", normalized to a tz-aware datetime (or None where the provider's
index can't say).

Each PROVIDER is the path segment its provider's captures land under, so
it has to match the package the leaf commands import it from -- a rename of
one without the other would silently redirect a whole provider's cache.
"""

from datetime import datetime, timezone

from chatfs.provider.aistudio import layout as aistudio_layout
from chatfs.provider.aistudio.types import IndexItem as AistudioIndexItem
from chatfs.provider.chatgpt import layout as chatgpt_layout
from chatfs.provider.chatgpt.types import IndexItem as ChatgptIndexItem
from chatfs.provider.claude import layout as claude_layout
from chatfs.provider.claude.types import IndexItem as ClaudeIndexItem


class DescribeProviderConstant:
    def it_matches_the_package_it_lives_in(self):
        assert (
            aistudio_layout.PROVIDER,
            chatgpt_layout.PROVIDER,
            claude_layout.PROVIDER,
        ) == ("aistudio", "chatgpt", "claude")


class DescribeUpdatedAt:
    """Every provider's index carries some last-changed timestamp under its
    own name; a consumer comparing it against a local capture's mtime must
    not have to know which provider it came from."""

    class WhenClaude:
        def it_parses_the_iso_8601_updated_at(self):
            item = ClaudeIndexItem(
                uuid="abc123",
                name="Hello",
                created_at="2026-07-17T02:00:00.000000Z",
                updated_at="2026-07-17T02:22:13.883559Z",
            )
            assert claude_layout.updated_at(item) == datetime(
                2026, 7, 17, 2, 22, 13, 883559, tzinfo=timezone.utc
            )

        def it_is_unknown_when_the_item_omits_the_field(self):
            item = ClaudeIndexItem(
                uuid="abc123", name="Hello", created_at="2026-07-17T02:00:00.000000Z"
            )
            assert claude_layout.updated_at(item) is None

    class WhenChatgpt:
        def it_parses_the_iso_8601_update_time(self):
            item = ChatgptIndexItem(
                id="abc123",
                title="Hello",
                create_time="2026-04-15T14:53:42.270850Z",
                update_time="2026-04-15T18:56:01.473026Z",
            )
            assert chatgpt_layout.updated_at(item) == datetime(
                2026, 4, 15, 18, 56, 1, 473026, tzinfo=timezone.utc
            )

        def it_is_unknown_when_the_item_omits_the_field(self):
            item = ChatgptIndexItem(
                id="abc123", title="Hello", create_time="2026-04-15T14:53:42.270850Z"
            )
            assert chatgpt_layout.updated_at(item) is None

    class WhenAistudio:
        def it_reads_last_modified_which_every_entry_carries(self):
            item = AistudioIndexItem(
                id="abc123", title="Hello", last_modified=1781977360
            )
            assert aistudio_layout.updated_at(item) == datetime(
                2026, 6, 20, 17, 42, 40, tzinfo=timezone.utc
            )
