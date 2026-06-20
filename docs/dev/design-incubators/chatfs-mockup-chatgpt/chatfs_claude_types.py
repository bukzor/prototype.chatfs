"""Shared types for the claude mockup."""

from typing import TypeGuard, TypedDict

from chatfs_json import JsonValue


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


class ChatMessage(TypedDict):
    """A node in the conversation tree, from conversation.json's `chat_messages`.

    Only the fields the renderer reads are declared; pass-through fields
    (sender, attachments, …) are present but ignored here.
    """

    uuid: str
    parent_message_uuid: str  # all-zero UUID sentinel for top-level messages
    created_at: str  # ISO 8601
    text: str  # flattened body; empty for a bodiless node (e.g. canceled retry)
    content: list[JsonValue]  # rich content blocks; empty alongside empty text


class Conversation(TypedDict):
    """The conversation.json payload — the subset the renderer reads."""

    chat_messages: list[ChatMessage]
    current_leaf_message_uuid: str


def is_chat_message(value: JsonValue) -> TypeGuard[ChatMessage]:
    return (
        isinstance(value, dict)
        and isinstance(value.get("uuid"), str)
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
