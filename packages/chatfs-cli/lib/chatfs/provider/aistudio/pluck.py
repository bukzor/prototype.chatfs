"""Wire knowledge for AI Studio's conversation/index pluck: URL patterns and
the CDP-response filters built on chatfs.pluck's shared skeleton.

AI Studio's source is JSPB (positional arrays), so each pluck also
unwraps and guards the envelope shape before yielding — more than the
other two providers' plucks need.
"""

import re
from collections.abc import Iterable, Iterator

from chatfs.json import JsonValue, is_json_array
from chatfs.pluck import iter_responses_matching

# ResolveDriveResource resolves any Drive resource, not just prompts, so URL
# alone doesn't guarantee a prompt body — pluck_conversation guards on shape
# too.
CONVERSATION_URL = re.compile(r"[./]MakerSuiteService/ResolveDriveResource$")
INDEX_URL = re.compile(r"[./]MakerSuiteService/ListPrompts$")


def pluck_conversation(cdp_lines: Iterable[str]) -> Iterator[JsonValue]:
    """Pluck each prompt message out of a ResolveDriveResource response body.

    AI Studio prompts are Drive-backed; the whole conversation arrives in
    this RPC as application/json+protobuf (JSPB — positional arrays, not
    keyed objects). Guards on shape, not just URL: the first message's
    `[0]` is `"prompts/<id>"`; yielding each envelope element flattens to
    one message per line (mirrors the old `.jq`'s `.[]`).
    """
    for envelope in iter_responses_matching(cdp_lines, CONVERSATION_URL):
        assert is_json_array(envelope), envelope
        first = envelope[0] if envelope else None
        first_id = first[0] if is_json_array(first) and first else ""
        if not (isinstance(first_id, str) and first_id.startswith("prompts/")):
            continue
        yield from envelope


def pluck_index_pages(cdp_lines: Iterable[str]) -> Iterator[JsonValue]:
    """Pluck each ListPrompts index entry, one per line.

    A response body is the JSPB envelope `[[<entry>, ...]]`; flattening
    `envelope[0]` yields individual entries so downstream doesn't need to
    know how many response bodies were captured (i.e. doesn't need to
    care about pagination — see chatfs.provider.aistudio.index.splat).
    Entries share ResolveDriveResource's PROMPT/METADATA schema (see
    chatfs.provider.aistudio.conversation.massage_json) with an empty
    chunkedPrompt (index entries carry no turn content).
    """
    for envelope in iter_responses_matching(cdp_lines, INDEX_URL):
        assert is_json_array(envelope) and envelope, envelope
        entries = envelope[0]
        assert is_json_array(entries), entries
        yield from entries
