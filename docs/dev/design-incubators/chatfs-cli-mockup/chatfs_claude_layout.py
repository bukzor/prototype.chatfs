"""Provider adapter for the claude mockup — see chatfs_layout for the
shared storage/view-tree helpers this wraps.
"""

from datetime import datetime
from pathlib import Path

from chatfs_claude_types import IndexItem
from chatfs_layout import (
    DATA_DIR_NAME,
    chat_dir_for,
    data_dir_for,
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
]

HERE = Path(__file__).parent
CONVERSATION_PLUCK = HERE / "chatfs_claude_conversation_pluck.jq"


def _created(created_at: str) -> datetime:
    """Parse claude's created_at.

    Claude's index returns `created_at` as an ISO 8601 string only;
    no epoch-float variant to handle.
    """
    return datetime.fromisoformat(created_at.replace("Z", "+00:00"))


def capture(url: str, chat_dir: Path) -> Path:
    return _capture(url, chat_dir, CONVERSATION_PLUCK)


def place_meta(item: IndexItem, root: Path) -> Path:
    return _place_meta(item["uuid"], item["name"], _created(item["created_at"]), item, root)
