"""Provider adapter for the chatgpt mockup — pure chatgpt-shaped knowledge:
URL <-> uuid conversion and create_time parsing. See chatfs.layout for the
shared storage/view-tree vocabulary and chatfs.shell.{capture,place} for the
side-effecting operations built on it.
"""
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from chatfs.provider.chatgpt.pluck import pluck_conversation
from chatfs.provider.chatgpt.types import IndexItem
from chatfs.shell.capture import capture as _capture
from chatfs.shell.place import place_meta as _place_meta


def url_for(uuid: str) -> str:
    return f"https://chatgpt.com/c/{uuid}"


def uuid_from_url(url: str) -> str:
    parts = urlparse(url).path.strip("/").split("/")
    assert len(parts) == 2 and parts[0] == "c", url
    return parts[1]


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
    """Write meta.json into `.data/$UUID/`, refresh the view dir-symlink.

    Returns the chat dir.
    """
    return _place_meta(item["id"], item["title"], created_at(item["create_time"]), item, root)
