"""Shared types for the chatgpt mockup."""
from typing import TypedDict


class IndexItem(TypedDict):
    """A conversation entry from /backend-api/conversations.

    Only the fields we read are declared; the dict carries many more
    pass-through fields (pinned_time, mapping, gizmo_id, …) that get
    serialized verbatim into `meta.json`.
    """

    id: str
    title: str
    create_time: str  # ISO 8601 UTC, e.g. "2026-04-15T14:53:42.270850Z"
