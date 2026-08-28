"""Shared CDP-filtering skeleton every provider's conversation/index pluck
is built on.
"""

import re
from collections.abc import Iterable, Iterator

import typed_json
from typed_json import JsonValue


def iter_responses(
    cdp_lines: Iterable[str], url_pattern: re.Pattern[str]
) -> Iterator[tuple[str, JsonValue]]:
    """Filter CDP capture lines to matching `Network.responseReceived`
    events, yielding `(url, parsed body)` per event.

    The skeleton shared by every provider's conversation/index pluck:
    select events whose response URL matches `url_pattern`, then
    string-guard the body before parsing it as JSON -- a 204 or
    interrupted response carries a non-string (`null`) body, so it's
    silently skipped here, same as the old `*.jq` filters' `| strings |`
    stage skipped it.

    The URL comes along because a paginated document links its pages
    through the *request* -- chatgpt's `?before=<cursor>` -- so a pluck
    that has to reassemble one needs more than the bodies.
    """
    for line in cdp_lines:
        if not line.strip():
            continue
        event = typed_json.loads(line)
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
        yield url, typed_json.loads(body)


def iter_response_bodies(
    cdp_lines: Iterable[str], url_pattern: re.Pattern[str]
) -> Iterator[JsonValue]:
    """The bodies alone, for plucks whose provider delivers what they
    want in a response the URL already identifies.

    Yields one parsed body per matching event; a provider's own pluck
    module handles any further per-provider reshaping (AI Studio's
    envelope flatten/guard; see `chatfs.provider.aistudio.pluck`).
    """
    for _url, body in iter_responses(cdp_lines, url_pattern):
        yield body
