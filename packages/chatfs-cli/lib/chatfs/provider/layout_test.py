"""Each PROVIDER is the path segment its provider's captures land under, so
it has to match the package the leaf commands import it from -- a rename of
one without the other would silently redirect a whole provider's cache."""

from chatfs.provider.aistudio import layout as aistudio_layout
from chatfs.provider.chatgpt import layout as chatgpt_layout
from chatfs.provider.claude import layout as claude_layout


class DescribeProviderConstant:
    def it_matches_the_package_it_lives_in(self):
        assert (
            aistudio_layout.PROVIDER,
            chatgpt_layout.PROVIDER,
            claude_layout.PROVIDER,
        ) == ("aistudio", "chatgpt", "claude")
