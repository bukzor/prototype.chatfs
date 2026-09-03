"""Provider adapter for the claude mockup — pure claude-shaped knowledge:
URL <-> uuid conversion and index timestamp parsing. See chatfs.layout for
the shared storage/view-tree vocabulary and chatfs.shell.{capture,place}
for the side-effecting operations built on it.
"""

from datetime import datetime
from typing import Final
from urllib.parse import urlparse

from chatfs.provider.claude.types import IndexItem


HOST: Final = "claude.ai"
"""The web host this provider serves conversations from -- the half of a
URL that identifies which provider a link belongs to."""

PROVIDER: Final = "claude"
"""This provider's path segment under a cache root (`chatfs.cli.extract_cache`)."""


def url_for(uuid: str) -> str:
    return f"https://{HOST}/chat/{uuid}"


def uuid_from_url(url: str) -> str:
    parts = urlparse(url).path.strip("/").split("/")
    assert len(parts) == 2 and parts[0] == "chat", url
    return parts[1]


def created_at(value: str) -> datetime:
    """Parse claude's created_at.

    Claude's index returns `created_at` as an ISO 8601 string only;
    no epoch-float variant to handle.
    """
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def updated_at(item: IndexItem) -> datetime | None:
    """When claude last changed this conversation, per its index.

    None when the item omits `updated_at` -- an answer of "can't judge
    this one", never a crash, since the field isn't guaranteed by the
    type guards that gate the splat.
    """
    value = item.get("updated_at")
    return created_at(value) if value is not None else None
