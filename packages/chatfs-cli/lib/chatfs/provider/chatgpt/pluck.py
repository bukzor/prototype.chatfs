"""Wire knowledge for chatgpt's conversation/index pluck: URL patterns and
the CDP-response filters built on chatfs.pluck's shared skeleton.
"""

import re
from collections.abc import Iterable, Iterator

from chatfs.json import JsonValue
from chatfs.pluck import iter_responses_matching

# Excludes sub-paths like /stream_status, /textdocs, /init.
CONVERSATION_URL = re.compile(r"/backend-api/conversation/[0-9a-f-]+$")
INDEX_URL = re.compile(r"/backend-api/conversations\?")


def pluck_conversation(cdp_lines: Iterable[str]) -> Iterator[JsonValue]:
    """Pluck the /backend-api/conversation/{id} response body."""
    return iter_responses_matching(cdp_lines, CONVERSATION_URL)


def pluck_index_pages(cdp_lines: Iterable[str]) -> Iterator[JsonValue]:
    """Pluck each /backend-api/conversations?... response body."""
    return iter_responses_matching(cdp_lines, INDEX_URL)
