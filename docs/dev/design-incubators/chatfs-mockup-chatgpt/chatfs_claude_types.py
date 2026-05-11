"""Shared types for the claude mockup."""
from typing import TypedDict


class IndexItem(TypedDict):
    """A conversation entry from /api/organizations/<org>/chat_conversations_v2.

    Only the fields we read are declared; the dict carries pass-through
    fields (summary, model, settings, is_starred, project_uuid, …) that
    get serialized verbatim into `meta.json`.
    """

    uuid: str
    name: str
    created_at: str  # ISO 8601 UTC, e.g. "2026-05-10T15:41:14.405121Z"
