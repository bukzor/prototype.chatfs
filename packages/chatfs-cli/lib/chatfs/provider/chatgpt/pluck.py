"""Wire knowledge for chatgpt's conversation/index pluck: URL patterns and
the CDP-response filters built on chatfs.pluck's shared skeleton.
"""

import re
from collections.abc import Iterable, Iterator

from typed_json import JsonValue
from chatfs.pluck import iter_response_bodies, iter_responses

# Matches every response that carries conversation content, across both
# shapes chatgpt serves it in: the whole-document `/conversation/{id}`
# and the paginated `/conversations/{id}` plus its `/messages` pages.
# Requiring `?` or end-of-string after the id excludes the sub-resources
# that share the prefix -- /stream_status, /textdocs, /init.
CONVERSATION_URL = re.compile(r"/backend-api/conversations?/[0-9a-f-]+(?:/messages)?(?:\?|$)")
INDEX_URL = re.compile(r"/backend-api/conversations\?")


def pluck_conversation(cdp_lines: Iterable[str]) -> Iterator[JsonValue]:
    """Pluck each conversation-bearing response body, tagged with its URL.

    One record per response rather than one document, because chatgpt
    may deliver a conversation across several: reassembling them is
    `chatfs.provider.chatgpt.conversation.assemble`'s job, and the page
    links it needs are in the request URLs, not the bodies.
    """
    for url, body in iter_responses(cdp_lines, CONVERSATION_URL):
        yield {"url": url, "body": body}


def pluck_index_pages(cdp_lines: Iterable[str]) -> Iterator[JsonValue]:
    """Pluck each /backend-api/conversations?... response body."""
    return iter_response_bodies(cdp_lines, INDEX_URL)
