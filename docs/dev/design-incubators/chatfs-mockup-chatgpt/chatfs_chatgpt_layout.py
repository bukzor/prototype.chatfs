"""Shared layout helpers for the chatgpt mockup.

Per-conversation directories live at:

    $root/YYYY/MM/DD/HH:MM:SS/

Each contains `meta.json` and a broken `$TITLE.md` self-symlink whose
target is its own basename (so dereferencing yields ELOOP — the title
is visible in `ls` while signalling "not yet materialized").
"""
import json
import os
from datetime import datetime
from pathlib import Path

from chatfs_chatgpt_types import IndexItem


def safe_filename(name: str) -> str:
    return name.replace("/", "∕").replace("\x00", "")


def time_dir_for(create_time: str) -> Path:
    dt = datetime.fromisoformat(create_time.replace("Z", "+00:00"))
    return Path(f"{dt:%Y/%m/%d/%H:%M:%S}")


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
