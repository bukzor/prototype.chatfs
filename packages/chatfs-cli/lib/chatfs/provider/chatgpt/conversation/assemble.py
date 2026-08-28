#!/usr/bin/env python3
"""Assemble chatgpt's conversation responses into one whole document.

Usage:
    chatfs-provider-chatgpt-conversation-assemble

Input (stdin): `conversation.json.d/raw.jsonl` -- one `{"url", "body"}`
record per conversation-bearing response, in capture order, as plucked
by `chatfs.provider.chatgpt.pluck.pluck_conversation`.

Output (stdout): `conversation.json` -- a single-rooted `mapping` of
`{id, message, parent, children}` nodes plus the conversation's own
identity fields, the shape splat and render consume. See
`design.kb/040-design.kb/conversation-document-is-whole.md` for why the
stage exists and what it refuses to guess.

chatgpt serves a conversation in either of two shapes. One response
carrying `mapping` is already whole and passes through. Otherwise the
newest turns arrive in the conversation endpoint's own body and older
ones in `/messages?before=<cursor>` responses fired as the reader
scrolls back; those chain through `page_info` into a linear mapping.
"""
import sys
from collections.abc import Iterable, Mapping, Sequence
from urllib.parse import parse_qs, urlparse

from chatfs.provider.chatgpt import json
from chatfs.provider.chatgpt.json import JsonObj, JsonValue

# Carried by a page for its own delivery, not by the conversation: the
# assembled document states the same facts as `mapping` instead.
TRANSPORT_FIELDS = ("messages", "page_info")

# Page-scoped sidecars that accumulate rather than replace, so the
# assembled document is their union in conversation order.
MERGED_FIELDS = ("safe_urls", "blocked_urls")


def before_cursor(url: str) -> str | None:
    """The message id a `/messages` request paginates back from, if any.

    Pages link through the request, not the body -- this is the only
    thing that says which page precedes which.
    """
    before = parse_qs(urlparse(url).query).get("before")
    return before[0] if before else None


def as_object(value: JsonValue) -> JsonObj:
    assert isinstance(value, Mapping), value
    return value


def as_array(value: JsonValue) -> Sequence[JsonValue]:
    assert isinstance(value, Sequence) and not isinstance(value, str), value
    return value


def page_info(page: JsonObj) -> JsonObj:
    return as_object(page["page_info"])


def chain_pages(records: Sequence[JsonObj]) -> list[JsonObj]:
    """Every page of the conversation, oldest first.

    Walks `has_previous_page` back from the conversation endpoint's own
    body. A page the capture never saw ends the walk with a raise: the
    reader stopped scrolling before reaching the top, and a prefix of a
    conversation is not a conversation.
    """
    pages_by_before: dict[str, JsonObj] = {}
    head: JsonObj | None = None
    for record in records:
        body = as_object(record["body"])
        cursor = before_cursor(str(record["url"]))
        if cursor is None:
            head = body
        else:
            pages_by_before[cursor] = body

    assert head is not None, (
        f"no conversation document among {len(records)} plucked response(s)"
    )
    chain = [head]
    seen: set[str] = set()
    while page_info(chain[-1])["has_previous_page"]:
        cursor = str(page_info(chain[-1])["start_cursor"])
        assert cursor not in seen, f"pagination cycle at {cursor}"
        seen.add(cursor)
        assert cursor in pages_by_before, (
            f"capture holds only {len(chain)} of this conversation's pages: "
            "chatgpt loads older messages as you scroll, so scroll to the top "
            "of the conversation before clicking Done Capturing "
            f"(no page before message {cursor})"
        )
        chain.append(pages_by_before[cursor])
    chain.reverse()
    return chain


def link_messages(messages: Sequence[JsonObj]) -> JsonObj:
    """The messages as a mapping: each parents the next, the first is root.

    Carries exactly the branching the responses carried. These pages
    serve one thread, so this is a chain -- no branch is invented for
    turns the provider didn't send.
    """
    ids = [str(message["id"]) for message in messages]
    assert len(set(ids)) == len(ids), f"duplicate message id across pages: {ids}"
    return {
        id_: {
            "id": id_,
            "message": message,
            "parent": ids[i - 1] if i else None,
            "children": [ids[i + 1]] if i + 1 < len(ids) else [],
        }
        for i, (id_, message) in enumerate(zip(ids, messages))
    }


def merge_lists(pages: Sequence[JsonObj], field: str) -> list[JsonValue]:
    """One page-scoped list per conversation: union, in page order."""
    merged: list[JsonValue] = []
    for page in pages:
        for item in as_array(page.get(field, [])):
            if item not in merged:
                merged.append(item)
    return merged


def assemble(records: Sequence[JsonObj]) -> JsonObj:
    """One whole conversation document from the responses that carried it.

    A later response supersedes an earlier one for the same page, so a
    re-navigated capture assembles from its freshest bytes.
    """
    whole = [as_object(r["body"]) for r in records if "mapping" in as_object(r["body"])]
    if whole:
        return whole[-1]

    pages = chain_pages(records)
    messages = [as_object(m) for page in pages for m in as_array(page["messages"])]
    document = {
        key: value
        for key, value in pages[-1].items()
        if key not in TRANSPORT_FIELDS and key not in MERGED_FIELDS
    }
    document["mapping"] = link_messages(messages)
    for field in MERGED_FIELDS:
        merged = merge_lists(pages, field)
        if merged:
            document[field] = merged
    assert document["current_node"] in document["mapping"], (
        f"current_node {document['current_node']} is not among the "
        f"{len(messages)} assembled messages"
    )
    return document


def read_records(lines: Iterable[str]) -> list[JsonObj]:
    return [as_object(json.loads(line)) for line in lines if line.strip()]


def main() -> None:
    document = assemble(read_records(sys.stdin))
    json.dump(document, sys.stdout)
    _ = sys.stdout.write("\n")


if __name__ == "__main__":
    main()
