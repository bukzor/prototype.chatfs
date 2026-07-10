"""Provider adapter for the claude mockup — see chatfs_layout for the
shared storage/view-tree helpers this wraps.

`capture()` stays here (not shared yet): it's an orchestration helper
misfiled in "layout", tracked separately for the shared-capture()
unification (see `.claude/todo.kb/2026-07-03-000-cross-provider-data-flow-drift--pre-unification-fixes-vs-unification-scope.md`
§ "Solve by unification").
"""

import subprocess
import sys
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
    return _place_meta(item["uuid"], item["name"], _created(item["created_at"]), item, root)
