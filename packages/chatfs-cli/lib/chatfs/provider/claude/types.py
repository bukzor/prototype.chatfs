"""Shared types for the claude mockup."""

from typing import Literal, NotRequired, TypeGuard, TypedDict

from typed_json import JsonObject, JsonValue


type Several[T] = tuple[T, ...]
"""A read-only homogeneous sequence — covariant, unlike `list`, so a function
taking `Several[Base]` accepts a tuple of any subtype."""


class IndexItem(TypedDict):
    """A conversation entry from /api/organizations/<org>/chat_conversations_v2.

    Only the fields we read are declared; the dict carries pass-through
    fields (summary, model, settings, is_starred, project_uuid, …) that
    get serialized verbatim into `meta.json`.
    """

    uuid: str
    name: str
    created_at: str  # ISO 8601 UTC, e.g. "2026-05-10T15:41:14.405121Z"


class IndexPage(TypedDict):
    """One page of /chat_conversations_v2, as plucked into JSONL."""

    data: list[IndexItem]
    has_more: bool


class ThinkingSummary(TypedDict):
    summary: str


class TextBlock(TypedDict):
    type: Literal["text"]
    text: str


class ThinkingBlock(TypedDict):
    """`summaries` label the disclosure; `thinking` is the raw trace."""

    type: Literal["thinking"]
    thinking: str
    summaries: list[ThinkingSummary]


class ToolUseBlock(TypedDict):
    """A tool invocation. `message` is a human-readable status shown while the
    tool runs (e.g. "Generating ask_user_input_v0..."), distinct from `input`;
    when present it's typically just the tool name, so callers fall back to
    `name` when it's absent (observed: an `artifacts` call with no `message`
    key at all).

    The call's id lives in one of two places, or neither: a top-level `id`
    (the common shape), or `input["_tool_call_id"]` (observed 2026-06 on the
    shape that emits parallel calls), or nothing at all (older captures).
    `tool_call_id` in splat.py reads both; see `ToolResultBlock` for what
    pairing is possible in each case.
    """

    type: Literal["tool_use"]
    name: str
    input: JsonObject
    id: NotRequired[str]
    message: NotRequired[str]


class ToolResultBlock(TypedDict):
    """The result of one `tool_use`, correlated by `tool_use_id` when present.

    Three shapes occur, and which one you get is not the renderer's choice:

    - `tool_use_id` matching the use's `id` — the common shape, and the only
      one that makes pairing sound when several calls run in parallel.
    - no `tool_use_id`, results strictly alternating with uses — older
      captures; adjacency pairs them unambiguously.
    - no `tool_use_id`, several uses then several results — claude.ai's
      parallel-call shape as of 2026-06. The correspondence is *not*
      recoverable: observed results arrive in completion order, which is not
      call order (see `render_tool_run`).

    `content` shape is tool-defined (open-ended across integrations) — a bare
    string, a list of result items, or occasionally a single object — so it
    stays `JsonValue` rather than a narrower TypedDict.
    """

    type: Literal["tool_result"]
    content: JsonValue
    is_error: bool
    name: NotRequired[str]
    tool_use_id: NotRequired[str]


class TokenBudgetBlock(TypedDict):
    """An internal budget checkpoint claude.ai's export interleaves into
    `content` around tool calls. Carries only timestamps -- no text, no
    tool linkage -- so the renderer ignores it rather than rendering an
    empty section."""

    type: Literal["token_budget"]
    start_timestamp: str
    stop_timestamp: str


type ContentBlock = (
    TextBlock | ThinkingBlock | ToolUseBlock | ToolResultBlock | TokenBudgetBlock
)


class ChatMessage(TypedDict):
    """A node in the conversation tree, from conversation.json's `chat_messages`.

    Only the fields the renderer reads are declared; pass-through fields
    (attachments, …) are present but ignored here.
    """

    uuid: str
    sender: str
    parent_message_uuid: str  # all-zero UUID sentinel for top-level messages
    created_at: str  # ISO 8601
    text: str  # flattened body; empty for a bodiless node (e.g. canceled retry)
    content: list[ContentBlock]  # rich content blocks; empty alongside empty text


class Conversation(TypedDict):
    """The conversation.json payload — the subset the renderer reads.

    `current_leaf_message_uuid` is NotRequired: claude.ai omits it on a
    conversation with zero messages (a chat created and never used --
    legal, and not rare -- there's no leaf to name). Present whenever
    `chat_messages` is non-empty.
    """

    chat_messages: list[ChatMessage]
    current_leaf_message_uuid: NotRequired[str]


def is_index_item(value: JsonValue) -> TypeGuard[IndexItem]:
    return (
        isinstance(value, dict)
        and isinstance(value.get("uuid"), str)
        and isinstance(value.get("name"), str)
        and isinstance(value.get("created_at"), str)
    )


def is_index_page(value: JsonValue) -> TypeGuard[IndexPage]:
    if not isinstance(value, dict):
        return False
    data = value.get("data")
    return isinstance(data, list) and isinstance(value.get("has_more"), bool) and all(
        is_index_item(i) for i in data
    )


def is_chat_message(value: JsonValue) -> TypeGuard[ChatMessage]:
    return (
        isinstance(value, dict)
        and isinstance(value.get("uuid"), str)
        and isinstance(value.get("sender"), str)
        and isinstance(value.get("parent_message_uuid"), str)
        and isinstance(value.get("created_at"), str)
    )


def is_conversation(value: JsonValue) -> TypeGuard[Conversation]:
    if not isinstance(value, dict):
        return False
    messages = value.get("chat_messages")
    if not isinstance(messages, list):
        return False
    leaf = value.get("current_leaf_message_uuid")
    # A leaf is required once there's at least one message to be the leaf of;
    # an empty conversation has none and omits the key entirely.
    if messages and not isinstance(leaf, str):
        return False
    return all(is_chat_message(m) for m in messages)
