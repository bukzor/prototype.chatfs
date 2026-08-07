"""Shared CDP-filtering skeleton every provider's conversation/index pluck
is built on.
"""

import re
from collections.abc import Iterable, Iterator

from chatfs import json as chatfs_json
from chatfs.json import JsonValue


def iter_responses_matching(
    cdp_lines: Iterable[str], url_pattern: re.Pattern[str]
) -> Iterator[JsonValue]:
    """Filter CDP capture lines to matching `Network.responseReceived` bodies.

    The skeleton shared by every provider's conversation/index pluck:
    select events whose response URL matches `url_pattern`, then
    string-guard the body before parsing it as JSON — a 204 or
    interrupted response carries a non-string (`null`) body, so it's
    silently skipped here, same as the old `*.jq` filters' `| strings |`
    stage skipped it.

    Yields one parsed body per matching event; a provider's own pluck
    module handles any further per-provider reshaping (AI Studio's
    envelope flatten/guard; see `chatfs.provider.aistudio.pluck`).
    """
    for line in cdp_lines:
        if not line.strip():
            continue
        event = chatfs_json.loads(line)
        assert isinstance(event, dict), event
        if event.get("method") != "Network.responseReceived":
            continue
        params = event["params"]
        assert isinstance(params, dict), params
        response = params["response"]
        assert isinstance(response, dict), response
        url = response["url"]
        assert isinstance(url, str), url
        if not url_pattern.search(url):
            continue
        body = response.get("body")
        if not isinstance(body, str):
            continue
        yield chatfs_json.loads(body)
