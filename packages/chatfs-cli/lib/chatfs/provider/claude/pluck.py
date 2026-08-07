"""Wire knowledge for claude's conversation/index pluck: URL patterns and
the CDP-response filters built on chatfs.pluck's shared skeleton.
"""

import re
from collections.abc import Iterable, Iterator

from chatfs.json import JsonValue
from chatfs.pluck import iter_responses_matching

# The URL carries query params (tree, rendering_mode, etc.) so we anchor on
# end-of-path-segment, not end-of-url.
CONVERSATION_URL = re.compile(r"/chat_conversations/[0-9a-f-]+($|\?)")
INDEX_URL = re.compile(r"/chat_conversations_v2\?")


def pluck_conversation(cdp_lines: Iterable[str]) -> Iterator[JsonValue]:
    """Pluck the /chat_conversations/{id}?tree=True&... response body."""
    return iter_responses_matching(cdp_lines, CONVERSATION_URL)


def pluck_index_pages(cdp_lines: Iterable[str]) -> Iterator[JsonValue]:
    """Pluck each /chat_conversations_v2?... response body."""
    return iter_responses_matching(cdp_lines, INDEX_URL)
