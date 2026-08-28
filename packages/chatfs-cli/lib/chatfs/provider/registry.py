"""Which provider a locator belongs to.

The provider-dispatching commands (`chatfs-conversation-<locator>-<verb>`)
are the only callers: they answer "which provider?" from the argument the
user already typed, then hand the whole argv to that provider's own leaf.
Every fact here is declared by a provider's `layout`, so adding a provider
means editing one dict, not hunting for host tables.
"""

from typing import Final

from chatfs.provider.aistudio import layout as aistudio_layout
from chatfs.provider.chatgpt import layout as chatgpt_layout
from chatfs.provider.claude import layout as claude_layout

PROVIDER_BY_HOST: Final = {
    aistudio_layout.HOST: aistudio_layout.PROVIDER,
    chatgpt_layout.HOST: chatgpt_layout.PROVIDER,
    claude_layout.HOST: claude_layout.PROVIDER,
}

PROVIDERS: Final = frozenset(PROVIDER_BY_HOST.values())
