"""Shared layout helpers for the chatgpt mockup.

Per-conversation directories live at:

    $root/YYYY/MM/DD/HH:MM:SS±HH:MM/

Each contains `meta.json` and a broken `$TITLE.md` self-symlink whose
target is its own basename (so dereferencing yields ELOOP — the title
is visible in `ls` while signalling "not yet materialized").
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from chatfs_chatgpt_types import IndexItem


def safe_filename(name: str) -> str:
    return name.replace("/", "∕").replace("\x00", "")


def _iso_offset(dt: datetime) -> str:
    """Return ISO 8601 extended-form offset, e.g. '-05:00'.

    Computed directly from utcoffset() to avoid the glibc-only %:z and
    Python's variable-length %z (which can include seconds).
    """
    off = dt.utcoffset()
    assert off is not None, dt
    total_min = int(off.total_seconds() // 60)
    sign = "+" if total_min >= 0 else "-"
    h, m = divmod(abs(total_min), 60)
    return f"{sign}{h:02d}:{m:02d}"


def time_dir_for(create_time: str | float) -> Path:
    """Render an ISO 8601 path-friendly timestamp in system local time.

    Accepts both shapes ChatGPT returns:
    - str: index endpoint, e.g. '2026-04-15T14:53:42.270850Z'
    - float: conversation document, Unix seconds
    """
    if isinstance(create_time, (int, float)):
        dt = datetime.fromtimestamp(create_time, tz=timezone.utc).astimezone()
    else:
        dt = datetime.fromisoformat(create_time.replace("Z", "+00:00")).astimezone()
    return Path(f"{dt:%Y/%m/%d/%H:%M:%S}{_iso_offset(dt)}")


def place_meta(item: IndexItem, root: Path) -> Path:
    d = root / time_dir_for(item["create_time"])
    d.mkdir(parents=True, exist_ok=True)

    (d / "meta.json").write_text(json.dumps(item, indent=2) + "\n")

    link_name = safe_filename(item["title"]) + ".md"
    link_path = d / link_name
    if link_path.is_symlink() or link_path.exists():
        link_path.unlink()
    os.symlink(link_name, link_path)

    return d
