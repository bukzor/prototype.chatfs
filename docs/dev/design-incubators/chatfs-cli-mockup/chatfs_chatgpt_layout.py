"""Provider adapter for the chatgpt mockup — see chatfs_layout for the
shared storage/view-tree helpers this wraps.
"""
import re
from collections.abc import Iterable, Iterator
from datetime import datetime, timezone
from pathlib import Path

from chatfs_chatgpt_types import IndexItem
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
    "created_at",
    "place_meta",
    "pluck_conversation",
    "pluck_index_pages",
]

# Excludes sub-paths like /stream_status, /textdocs, /init.
CONVERSATION_URL = re.compile(r"/backend-api/conversation/[0-9a-f-]+$")
INDEX_URL = re.compile(r"/backend-api/conversations\?")


def pluck_conversation(cdp_lines: Iterable[str]) -> Iterator[JsonValue]:
    """Pluck the /backend-api/conversation/{id} response body."""
    return iter_responses_matching(cdp_lines, CONVERSATION_URL)


def pluck_index_pages(cdp_lines: Iterable[str]) -> Iterator[JsonValue]:
    """Pluck each /backend-api/conversations?... response body."""
    return iter_responses_matching(cdp_lines, INDEX_URL)


def created_at(create_time: str | float) -> datetime:
    """Parse chatgpt's create_time — both shapes it returns.

    - str: index endpoint, e.g. '2026-04-15T14:53:42.270850Z'
    - float: conversation document, Unix seconds
    """
    if isinstance(create_time, (int, float)):
        return datetime.fromtimestamp(create_time, tz=timezone.utc)
    else:
        return datetime.fromisoformat(create_time.replace("Z", "+00:00"))


def capture(url: str, chat_dir: Path) -> Path:
    return _capture(url, chat_dir, pluck_conversation)


def place_meta(item: IndexItem, root: Path) -> Path:
    """Write meta.json into .chat/$UUID/.data/, refresh the view dir-symlink.

    Returns the chat dir.
    """
    return _place_meta(item["id"], item["title"], created_at(item["create_time"]), item, root)
