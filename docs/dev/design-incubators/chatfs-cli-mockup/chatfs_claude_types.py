"""Shared types for the claude mockup."""

from typing import Literal, TypeGuard, TypedDict

from chatfs_json import JsonObject, JsonValue


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
    tool runs (e.g. "Generating ask_user_input_v0..."), distinct from `input`."""

    type: Literal["tool_use"]
    id: str
    name: str
    input: JsonObject
    message: str


class ToolResultBlock(TypedDict):
    """The result paired with a preceding `tool_use` (matched by `tool_use_id`).

    `content` shape is tool-defined (open-ended across integrations) — a bare
    string, a list of result items, or occasionally a single object — so it
    stays `JsonValue` rather than a narrower TypedDict.
    """

    type: Literal["tool_result"]
    tool_use_id: str
    content: JsonValue
    is_error: bool


type ContentBlock = TextBlock | ThinkingBlock | ToolUseBlock | ToolResultBlock


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
    """The conversation.json payload — the subset the renderer reads."""

    chat_messages: list[ChatMessage]
    current_leaf_message_uuid: str


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
    leaf = value.get("current_leaf_message_uuid")
    if not isinstance(messages, list) or not isinstance(leaf, str):
        return False
    return all(is_chat_message(m) for m in messages)
