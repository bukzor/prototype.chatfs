"""Shared layout helpers for the claude mockup.

Mirrors chatfs_chatgpt_layout.py with claude-shaped item keys
(uuid/name/created_at vs id/title/create_time). The two will likely
get factored into a provider-agnostic core once both pipelines run
end-to-end.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from chatfs_claude_types import IndexItem


HERE = Path(__file__).parent
CONVERSATION_PLUCK = HERE / "chatfs_claude_conversation_pluck.jq"
DATA_DIR_NAME = ".data"


def safe_filename(name: str) -> str:
    return name.replace("/", "∕").replace("\x00", "")


def _iso_offset(dt: datetime) -> str:
    off = dt.utcoffset()
    assert off is not None, dt
    total_min = int(off.total_seconds() // 60)
    sign = "+" if total_min >= 0 else "-"
    h, m = divmod(abs(total_min), 60)
    return f"{sign}{h:02d}:{m:02d}"


def time_dir_for(created_at: str) -> Path:
    """ISO 8601 path-friendly timestamp in system local time.

    Claude's index returns `created_at` as an ISO 8601 string only;
    no epoch-float variant to handle.
    """
    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00")).astimezone()
    return Path(f"{dt:%Y/%m/%d/%H:%M:%S}{_iso_offset(dt)}")


def chat_dir_for(uuid: str, root: Path) -> Path:
    return root / ".chat" / uuid


def data_dir_for(uuid: str, root: Path) -> Path:
    return chat_dir_for(uuid, root) / DATA_DIR_NAME


def resolve_chat_dir(arg: str | os.PathLike[str]) -> Path:
    p = Path(arg).resolve()
    if not p.is_dir():
        p = p.parent
    while p.parent.name != ".chat":
        assert p.parent != p, f"reached fs root without finding .chat: {arg}"
        p = p.parent
    assert p.is_dir(), p
    return p


def _purge_view_symlinks(uuid: str, root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_symlink() and uuid in os.readlink(path):
            path.unlink()


def capture(url: str, chat_dir: Path) -> Path:
    """Browse $url and pluck the conversation into chat_dir/.data/.

    Ensures `.data/` exists, clears any prior cdp.jsonl /
    conversation.json from a previous run, then runs har-browse
    followed by the conversation pluck. Returns the data dir for
    callers that need to deposit meta.json or similar siblings.

    The intermediate-data policy is the load-bearing piece: captures
    land directly in `.chat/$UUID/.data/`, never a tempdir. Failures
    leave the bytes inspectable; success hands off to splat/render
    without a move.
    """
    data_dir = chat_dir / DATA_DIR_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    cdp = data_dir / "cdp.jsonl"
    conversation = data_dir / "conversation.json"

    cdp.unlink(missing_ok=True)
    conversation.unlink(missing_ok=True)

    print(f"Capturing {url} → {cdp} ...", file=sys.stderr)
    with cdp.open("wb") as f:
        _ = subprocess.run(["har-browse", url], stdout=f, check=True)

    print(f"Plucking conversation → {conversation} ...", file=sys.stderr)
    with cdp.open("rb") as src, conversation.open("wb") as dst:
        _ = subprocess.run([str(CONVERSATION_PLUCK)], stdin=src, stdout=dst, check=True)

    return data_dir


def place_meta(item: IndexItem, root: Path) -> Path:
    uuid = item["uuid"]
    chat_dir = chat_dir_for(uuid, root)
    data_dir = chat_dir / DATA_DIR_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    _ = (data_dir / "meta.json").write_text(json.dumps(item, indent=2) + "\n")

    _purge_view_symlinks(uuid, root)

    view_dir = root / time_dir_for(item["created_at"])
    view_dir.mkdir(parents=True, exist_ok=True)

    title_link = view_dir / safe_filename(item["name"] or uuid)
    if title_link.is_symlink() or title_link.exists():
        title_link.unlink()
    title_link.symlink_to(os.path.relpath(chat_dir, start=view_dir))

    return chat_dir
