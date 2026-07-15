"""Provider adapter for the claude mockup — see chatfs_layout for the
shared storage/view-tree helpers this wraps.
"""

import re
from collections.abc import Iterable, Iterator
from datetime import datetime
from pathlib import Path

from chatfs_claude_types import IndexItem
from chatfs_json import JsonValue
from chatfs_layout import (
    DATA_DIR_NAME,
    chat_dir_for,
    data_dir_for,
    iter_responses_matching,
    resolve_chat_dir,
    safe_filename,
)
from chatfs_layout import capture as _capture
from chatfs_layout import place_meta as _place_meta

__all__ = [
    "DATA_DIR_NAME",
    "chat_dir_for",
    "data_dir_for",
    "resolve_chat_dir",
    "safe_filename",
    "capture",
    "place_meta",
    "pluck_conversation",
    "pluck_index_pages",
]

# The URL carries query params (tree, rendering_mode, etc.) so we anchor on
# end-of-path-segment, not end-of-url.
CONVERSATION_URL = re.compile(r"/chat_conversations/[0-9a-f-]+($|\?)")
INDEX_URL = re.compile(r"/chat_conversations_v2\?")


def pluck_conversation(cdp_lines: Iterable[str]) -> Iterator[JsonValue]:
    """Pluck the /chat_conversations/{id}?tree=True&... response body."""
    return iter_responses_matching(cdp_lines, CONVERSATION_URL)


def pluck_index_pages(cdp_lines: Iterable[str]) -> Iterator[JsonValue]:
    """Pluck each /chat_conversations_v2?... response body."""
    return iter_responses_matching(cdp_lines, INDEX_URL)


def _created(created_at: str) -> datetime:
    """Parse claude's created_at.

    Claude's index returns `created_at` as an ISO 8601 string only;
    no epoch-float variant to handle.
    """
    return datetime.fromisoformat(created_at.replace("Z", "+00:00"))


def capture(url: str, chat_dir: Path) -> Path:
    return _capture(url, chat_dir, pluck_conversation)


def place_meta(item: IndexItem, root: Path) -> Path:
    return _place_meta(item["uuid"], item["name"], _created(item["created_at"]), item, root)
