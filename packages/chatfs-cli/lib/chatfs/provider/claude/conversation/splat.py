#!/usr/bin/env python3
"""Splat a claude conversation JSON into a `messages/` directory.

Input: path to conversation.json (the plucked
`/chat_conversations/{id}?…` response body).

Output: `<src>.splat/messages/<basename>.{json,md}` per message in
`chat_messages`, or `<output-dir>/messages/...` when an output-dir
argument is given (only `messages/` is cleared/recreated -- sibling
content in an explicit output-dir, e.g. a caller-placed `.data`
symlink, is left alone). The .json carries the raw message object; the
.md carries the rendered content.

Scope: `text` blocks pass through; `thinking` and each correlated
`tool_use`+`tool_result` pair render as collapsible
`<details type="...">` sections (the `type` attribute makes each kind
greppable); `token_budget` is dropped (timestamps only, nothing to
show); a `tool_use` the user canceled before its result arrived (a
hollow trailing text block instead of a `tool_result`) renders as its
own collapsible, marked canceled; a parallel batch whose results can't
be correlated renders one collapsible per block, unfused (see
`render_tool_run`). A block type this parser doesn't recognize renders
as a `<details type="unmodeled">` dump of the raw block rather than
crashing the whole conversation's render; either case also warns on
stderr. The raw block stays in the .json regardless. No
`conversations/` branch-symlinks yet (next ladder rung).
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import typed_json
from typed_json import JsonObject, JsonValue
from chatfs.layout import safe_filename
from chatfs.provider.claude.types import (
    ChatMessage,
    ContentBlock,
    Several,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    is_conversation,
)
from chatfs.shell import sh as chatfs_sh


def format_timestamp(created_at: str) -> str:
    """ISO 8601 in local TZ, comma fractional, +HHMM offset.

    Matches chatgpt-splat's basename timestamp so messages/<stem> links
    are readable side-by-side with the chatgpt side. Claude `created_at`
    has microsecond precision; we pad to 9 digits.
    """
    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00")).astimezone()
    fractional = f"{dt.microsecond:06d}000"
    return dt.strftime(f"%Y-%m-%dT%H:%M:%S,{fractional}%z")


def fenced_json(value: object) -> str:
    return "```json\n" + json.dumps(value, indent=2, ensure_ascii=False) + "\n```"


def render_details(
    kind: str, icon: str, label: str, body: str, tool: str | None = None
) -> str:
    """Wrap non-answer content in a collapsible `<details>`, tagged for grep.

    `type="{kind}"` makes each block kind searchable (e.g.
    `grep 'type="tool_call"'`); `tool="{tool}"` further distinguishes
    tool calls by name. `<details>` (vs a blockquote) keeps the content
    collapsed-by-default and avoids colliding with the render step's
    blockquote-as-fork-depth convention.
    """
    tool_attr = f' tool="{tool}"' if tool else ""
    return (
        f'<details type="{kind}"{tool_attr}><summary>{icon} {label}</summary>'
        f"\n\n{body}\n\n</details>"
    )


def render_thinking(block: ThinkingBlock) -> str:
    """Render a `thinking` block. Claude's own `summaries` label the disclosure."""
    label = "; ".join(s["summary"] for s in block["summaries"])
    return render_details("thinking", "💭", label or "Thinking", block["thinking"].strip())


def render_result_content(content: JsonValue) -> str:
    """Render a tool_result `content` payload to markdown.

    Tool result schemas are open-ended (each tool returns its own item
    shape), so this dispatches on the item keys it knows — knowledge
    items (web search/fetch) become a link list, text items pass
    through — and falls back to JSON for anything unrecognized rather
    than dropping it.
    """
    match content:
        case str():
            return content.strip()
        case list():
            lines: list[str] = []
            for item in content:
                if not isinstance(item, dict):
                    lines.append(str(item))
                elif isinstance(text := item.get("text"), str) and text:
                    lines.append(text.strip())
                elif isinstance(title := item.get("title"), str):
                    url = item.get("url")
                    lines.append(f"- [{title}]({url})" if isinstance(url, str) else f"- {title}")
                else:
                    lines.append(fenced_json(item))
            return "\n".join(lines)
        case _:
            return fenced_json(content)


def warn_unmodeled_input_keys(name: str, tool_input: JsonObject, modeled: frozenset[str]) -> None:
    """Warn -- don't raise -- when a tool_input carries keys we don't model.

    claude.ai adds optional tool parameters over time: `web_fetch` grew
    `text_content_token_limit` (observed 2025-12) and then
    `html_extraction_method` (2026-08). The wire format permits them, so
    per technical-policy.kb's robustness target they're required work,
    not defensive work.

    Only the modeled keys feed the rendered label, so an unmodeled key
    costs nothing to ignore. Raising on one costs the whole
    conversation's render. That trade sits at the consumer end of the
    pipeline, where zero-data-loss explicitly permits filtering on read:
    the capture is already safe on disk and the render is redoable. Loud,
    not fatal.
    """
    unmodeled = set(tool_input) - modeled
    if unmodeled:
        print(
            f"warning: unmodeled {name} tool_input keys, ignored: {sorted(unmodeled)}",
            file=sys.stderr,
        )


TOOL_ICONS = {"web_search": "🔍", "web_fetch": "🕷️"}
"""Per-tool disclosure icon; anything unlisted gets the generic wrench."""


def tool_icon(name: str | None) -> str:
    return TOOL_ICONS.get(name or "", "🛠️")


def tool_label(use: ToolUseBlock) -> str:
    """The disclosure summary for a `tool_use`: its one salient argument.

    web_search/web_fetch each have a single argument worth reading, so it
    stands alone as the label and the request JSON is dropped from the body.
    Any other tool has no argument we can name, so the label carries the
    tool's own status `message` and the body keeps the request verbatim.
    """
    name = use["name"]
    tool_input = use["input"]
    match name:
        case "web_search":
            warn_unmodeled_input_keys(name, tool_input, frozenset({"query", "_tool_call_id"}))
            assert "query" in tool_input, tool_input
            query = tool_input["query"]
            assert isinstance(query, str), query
            return query
        case "web_fetch":
            # Only `url` feeds the label; the rest are caller-side knobs
            # (`text_content_token_limit` caps the excerpt,
            # `html_extraction_method` picks the parse, `_tool_call_id`
            # identifies the call). See warn_unmodeled_input_keys for why new
            # ones warn instead of raise.
            warn_unmodeled_input_keys(
                name,
                tool_input,
                frozenset({
                    "url",
                    "text_content_token_limit",
                    "html_extraction_method",
                    "_tool_call_id",
                }),
            )
            assert "url" in tool_input, tool_input
            url = tool_input["url"]
            assert isinstance(url, str), url
            return url
        case _:
            return f"{name} — {use.get('message', name)}"


def render_tool_call(use: ToolUseBlock, result: ToolResultBlock) -> str:
    """Render a `tool_use` + the `tool_result` known to be its own, fused into
    one collapsible tagged `tool="<name>"`.

    Fusing asserts a correspondence, so the caller may only pair blocks it
    can actually correlate -- see `render_tool_run`. web_search/web_fetch
    show the result under a summary built from their single argument; other
    tools show the request JSON above the result.
    """
    name = use["name"]
    result_md = render_result_content(result["content"])
    error = " — ERROR" if result["is_error"] else ""
    label = tool_label(use) + error

    if name in TOOL_ICONS:
        body = result_md
    else:
        body = f"**Request:**\n\n{fenced_json(use['input'])}\n\n**Result:**\n\n{result_md}"
    return render_details("tool_call", tool_icon(name), label, body, tool=name)


def render_tool_request(use: ToolUseBlock) -> str:
    """Render a `tool_use` whose result we cannot name -- the request alone.

    Used where fusing would be a guess: a parallel batch whose results carry
    no id, or a call whose result never arrived. The request JSON is kept
    verbatim (`_tool_call_id` included) so nothing the capture holds is lost
    on the way to the page.
    """
    name = use["name"]
    label = f"{tool_label(use)} — request"
    body = f"**Request:**\n\n{fenced_json(use['input'])}"
    return render_details("tool_call", tool_icon(name), label, body, tool=name)


def render_tool_result(result: ToolResultBlock) -> str:
    """Render a `tool_result` we cannot attribute to a particular call."""
    name = result.get("name")
    error = " — ERROR" if result["is_error"] else ""
    label = f"{name or 'tool'} — result{error}"
    body = render_result_content(result["content"])
    return render_details("tool_call", tool_icon(name), label, body, tool=name or "")


def render_interrupted_tool_call(use: ToolUseBlock) -> str:
    """Render a `tool_use` the user canceled before its `tool_result` arrived.

    claude.ai's export marks this the same way it marks a bodiless
    `user_canceled` retry (see `has_body` in render.py): a single hollow
    `{"type":"text","text":""}` block, here trailing the tool call instead
    of standing alone as the whole message.
    """
    name = use["name"]
    label = f"{name} — {use.get('message', name)} — canceled"
    body = f"**Request:**\n\n{fenced_json(use['input'])}\n\n_(canceled before result)_"
    return render_details("tool_call", "🛠️", label, body, tool=name)


def tool_call_id(use: ToolUseBlock) -> str | None:
    """The call's id, from either place claude.ai puts it (see ToolUseBlock)."""
    top = use.get("id")
    if isinstance(top, str):
        return top
    nested = use["input"].get("_tool_call_id")
    return nested if isinstance(nested, str) else None


def pair_by_id(
    uses: Several[ToolUseBlock], results: Several[ToolResultBlock]
) -> list[tuple[ToolUseBlock, ToolResultBlock | None]] | None:
    """Match each use to its result by id, in call order. `None` when the ids
    can't do the job -- a missing or duplicate id on either side, or a result
    naming a call that isn't in this run.

    An id present on both sides is the only sound correlation; returning
    `None` rather than guessing is what keeps a mispaired render impossible.
    """
    ids = [tool_call_id(use) for use in uses]
    if None in ids or len(set(ids)) != len(ids):
        return None
    result_of: dict[str, ToolResultBlock] = {}
    for result in results:
        rid = result.get("tool_use_id")
        if not isinstance(rid, str) or rid not in ids or rid in result_of:
            return None
        result_of[rid] = result
    return [(use, result_of.get(rid)) for use, rid in zip(uses, ids) if rid is not None]


def split_tool_run(
    blocks: Several[ContentBlock], start: int
) -> tuple[list[ToolUseBlock], list[ToolResultBlock]]:
    """The run of consecutive `tool_use` blocks at `start`, plus the run of
    `tool_result` blocks immediately following it.

    A run is the unit of pairing because that's the unit claude.ai emits:
    one use then one result in the sequential case, N uses then N results
    when the calls ran in parallel.
    """
    uses: list[ToolUseBlock] = []
    results: list[ToolResultBlock] = []
    i = start
    while i < len(blocks):
        use = blocks[i]
        if use["type"] != "tool_use":
            break
        uses.append(use)
        i += 1
    while i < len(blocks):
        result = blocks[i]
        if result["type"] != "tool_result":
            break
        results.append(result)
        i += 1
    return uses, results


def render_tool_run(
    uses: Several[ToolUseBlock], results: Several[ToolResultBlock]
) -> list[str]:
    """Render one run of tool calls and their results, fusing only what we can
    correlate.

    Ids win when both sides carry them. Failing that, a lone use and a lone
    result pair by adjacency -- unambiguous, and how every pre-2026 capture
    reads. Everything else stays unfused: claude.ai's parallel-call shape
    (2026-06) drops the ids and emits results in completion order, observed
    reversed against call order, so positional fusing there would caption one
    query with another query's hits. An unfused run loses nothing -- every
    block still renders, just under its own disclosure.
    """
    pairs = pair_by_id(uses, results)
    if pairs is None and len(uses) == 1 and len(results) == 1:
        pairs = [(uses[0], results[0])]
    if pairs is None:
        counts = f"{len(uses)} tool call(s) and {len(results)} result(s)"
        print(f"warning: {counts} carry no matching ids; rendering them unpaired", file=sys.stderr)
        return [render_tool_request(u) for u in uses] + [render_tool_result(r) for r in results]
    return [
        render_tool_call(use, result) if result is not None else render_tool_request(use)
        for use, result in pairs
    ]


def extract_text(content_blocks: Several[ContentBlock]) -> str:
    """Render content blocks to markdown, in document order.

    `text` passes through; `thinking` and each tool call become collapsible
    `<details>`. Order is preserved so reasoning and tool calls sit where
    they happened, around the answer they produced. A block type this parser
    doesn't recognize renders as a raw-JSON `<details type="unmodeled">`
    rather than vanishing or crashing the render -- the wire format is a
    third party's and unversioned, so a fresh block type is expected drift,
    not a bug; an uncorrelatable tool call renders unfused rather than
    raising -- see `render_tool_run`.
    """
    pieces: list[str] = []
    i = 0
    while i < len(content_blocks):
        block = content_blocks[i]
        match block:
            case {"type": "text", "text": text}:
                if text:  # empty text blocks occur; skip them
                    pieces.append(text)
            case {"type": "thinking"}:
                pieces.append(render_thinking(block))
            case {"type": "token_budget"}:
                pass  # timestamps only, nothing to show
            case {"type": "tool_use"}:
                uses, results = split_tool_run(content_blocks, i)
                end = i + len(uses) + len(results)
                trailing = content_blocks[end] if end == len(content_blocks) - 1 else None
                match trailing:
                    case {"type": "text", "text": ""} if not results and len(uses) == 1:
                        # user_canceled mid-call: the same hollow marker
                        # has_body/normalize_bodiless_nodes treat as a canceled
                        # retry, here trailing a tool call instead of standing
                        # alone -- no tool_result ever arrived.
                        pieces.append(render_interrupted_tool_call(uses[0]))
                        end += 1  # consume the hollow placeholder too
                    case _:
                        pieces.extend(render_tool_run(tuple(uses), tuple(results)))
                i = end - 1  # the loop's own increment lands on the next block
            case {"type": "tool_result"}:
                # A tool_result with no preceding tool_use in this message --
                # not a shape render_tool_result doesn't already handle (it's
                # built for exactly "a tool_result we can't attribute to a
                # call"), just an unexpected position for it.
                print(
                    "warning: tool_result with no preceding tool_use in this message; rendering unfused",
                    file=sys.stderr,
                )
                pieces.append(render_tool_result(block))
            case _:
                kind = block["type"]
                print(
                    f"warning: unmodeled content block type, passed through: {kind!r}",
                    file=sys.stderr,
                )
                pieces.append(
                    render_details("unmodeled", "❓", f"Unrecognized content: {kind}", fenced_json(block))
                )
        i += 1
    return "\n\n".join(pieces)


def basename_for(msg: ChatMessage) -> str:
    return safe_filename(
        f"{format_timestamp(msg['created_at'])}.{msg['sender']}.{msg['uuid']}"
    )


def load_conversation_json(src: Path) -> JsonValue:
    """Load a conversation.json, tolerating a duplicate-capture artifact.

    Observed once (3e52c1b9): a capture wrote the same conversation twice,
    concatenated with no separator. Parse the first complete object and warn
    rather than crash on "Extra data" -- but only when the trailing bytes are
    themselves a second JSON value; anything else means the file is actually
    corrupt, and `json.loads` below raises for that case same as always.
    """
    text = src.read_text()
    _, end = json.JSONDecoder().raw_decode(text)
    trailing = text[end:].strip()
    if not trailing:
        return typed_json.loads(text)
    json.loads(trailing)  # raises if trailing isn't valid JSON on its own
    print(
        f"warning: {src} has trailing JSON data after the first object "
        f"({len(trailing)} bytes) -- using the first object, discarding the rest",
        file=sys.stderr,
    )
    return typed_json.loads(text[:end])


def splat(src: Path, base_dir: Path) -> tuple[int, int]:
    """Splat src's conversation into base_dir/messages/.

    Returns (message count, rendered-with-body count)."""
    import shutil

    doc = load_conversation_json(src)
    assert is_conversation(doc), doc
    chat_messages = doc["chat_messages"]

    messages_dir = base_dir / "messages"
    if messages_dir.exists():
        shutil.rmtree(messages_dir)
    messages_dir.mkdir(parents=True)

    rendered_count = 0
    for msg in chat_messages:
        basename = basename_for(msg)
        _ = (messages_dir / f"{basename}.json").write_text(
            json.dumps(msg, indent=2, ensure_ascii=False) + "\n"
        )
        text = extract_text(tuple(msg["content"]))
        if text:
            _ = (messages_dir / f"{basename}.md").write_text(text + "\n")
            rendered_count += 1

    return len(chat_messages), rendered_count


def main() -> None:
    import sys

    if len(sys.argv) not in (2, 3):
        print(f"Usage: {sys.argv[0]} <conversation.json> [output-dir]", file=sys.stderr)
        sys.exit(1)

    src = Path(sys.argv[1])
    base_dir = Path(sys.argv[2]) if len(sys.argv) == 3 else src.with_suffix(".splat")
    total, rendered_count = splat(src, base_dir)

    chatfs_sh.log(
        f"wrote {total} message(s), {rendered_count} with rendered "
        + f"content, to {base_dir}"
    )


if __name__ == "__main__":
    main()
