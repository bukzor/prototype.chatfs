"""Provider adapter for the claude mockup — pure claude-shaped knowledge:
URL <-> uuid conversion and index timestamp parsing. See chatfs.layout for
the shared storage/view-tree vocabulary and chatfs.shell.{capture,place}
for the side-effecting operations built on it.
"""

from datetime import datetime
from urllib.parse import urlparse


def url_for(uuid: str) -> str:
    return f"https://claude.ai/chat/{uuid}"


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
