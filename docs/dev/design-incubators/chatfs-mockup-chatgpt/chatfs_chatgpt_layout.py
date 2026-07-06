"""Provider adapter for the chatgpt mockup — see chatfs_layout for the
shared storage/view-tree helpers this wraps.
"""
from datetime import datetime, timezone
from pathlib import Path

from chatfs_chatgpt_types import IndexItem
from chatfs_layout import (
    DATA_DIR_NAME,
    chat_dir_for,
    data_dir_for,
    resolve_chat_dir,
    safe_filename,
)
from chatfs_layout import place_meta as _place_meta

__all__ = [
    "DATA_DIR_NAME",
    "chat_dir_for",
    "data_dir_for",
    "resolve_chat_dir",
    "safe_filename",
    "place_meta",
]


def _created(create_time: str | float) -> datetime:
    """Parse chatgpt's create_time — both shapes it returns.

    - str: index endpoint, e.g. '2026-04-15T14:53:42.270850Z'
    - float: conversation document, Unix seconds
    """
    if isinstance(create_time, (int, float)):
        return datetime.fromtimestamp(create_time, tz=timezone.utc)
    return datetime.fromisoformat(create_time.replace("Z", "+00:00"))


def place_meta(item: IndexItem, root: Path) -> Path:
    """Write meta.json into .chat/$UUID/.data/, refresh the view dir-symlink.

    Returns the chat dir.
    """
    return _place_meta(item["id"], item["title"], _created(item["create_time"]), item, root)
