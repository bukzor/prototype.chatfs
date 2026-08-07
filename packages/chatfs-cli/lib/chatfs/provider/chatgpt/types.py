"""Shared types for the chatgpt mockup."""
from typing import NotRequired, TypedDict, TypeGuard

from chatfs.json import JsonValue


class IndexItem(TypedDict):
    """A conversation entry from /backend-api/conversations.

    Only the fields we read are declared; the dict carries many more
    pass-through fields (pinned_time, mapping, gizmo_id, …) that get
    serialized verbatim into `meta.json`.
    """

    id: str
    title: str
    create_time: str  # ISO 8601 UTC, e.g. "2026-04-15T14:53:42.270850Z"


class IndexPage(TypedDict):
    """One page of /backend-api/conversations, as plucked into JSONL."""

    items: list[IndexItem]


class Message(TypedDict):
    """A `mapping[uuid].message` entry in a conversation document.

    Many nodes are legitimately messageless (forks, system placeholders) --
    only the field conversation_render reads for dead-branch ordering is
    declared.
    """

    create_time: NotRequired[float | None]


class Node(TypedDict):
    """One entry in `conversation.mapping`, keyed by node uuid."""

    parent: NotRequired[str | None]
    children: NotRequired[list[str]]
    message: NotRequired[Message | None]


class Conversation(TypedDict):
    """The captured conversation.json payload -- a DAG of `Node`s plus the live leaf."""

    mapping: dict[str, Node]
    current_node: str


def is_index_item(value: JsonValue) -> TypeGuard[IndexItem]:
    return (
        isinstance(value, dict)
        and isinstance(value.get("id"), str)
        and isinstance(value.get("title"), str)
        and isinstance(value.get("create_time"), str)
    )


def is_index_page(value: JsonValue) -> TypeGuard[IndexPage]:
    if not isinstance(value, dict):
        return False
    items = value.get("items")
    return isinstance(items, list) and all(is_index_item(i) for i in items)


def is_node(value: JsonValue) -> TypeGuard[Node]:
    return isinstance(value, dict)


def is_conversation(value: JsonValue) -> TypeGuard[Conversation]:
    if not isinstance(value, dict):
        return False
    mapping = value.get("mapping")
    current_node = value.get("current_node")
    if not isinstance(mapping, dict) or not isinstance(current_node, str):
        return False
    return all(is_node(v) for v in mapping.values())
