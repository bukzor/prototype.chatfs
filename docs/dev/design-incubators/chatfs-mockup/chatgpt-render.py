#!/usr/bin/env python3
"""Render a conversation's current_node path into the $TITLE.md placeholder.

Walks from the root of `mapping` to `current_node` (the head pointer the
ChatGPT UI persists for "what the user is looking at"), emits one section
per message: a `## <role>` heading, a `<file:...>` autolink backref to
the atomic turn-file under $TIMESTAMP.splat/messages/, and the message
body if any.

Usage:
    chatgpt-render.py <path-inside-page-dir>
"""
import json
import sys
from collections.abc import Mapping
from pathlib import Path


def walk_to_current(mapping: Mapping[str, dict], current: str) -> list[str]:
    path: list[str] = []
    node = current
    while node is not None:
        path.append(node)
        node = mapping[node].get("parent")
    path.reverse()
    return path


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path-inside-page-dir>", file=sys.stderr)
        sys.exit(2)

    page = Path(sys.argv[1])
    if page.exists(follow_symlinks=False) and not page.is_dir():
        page = page.parent

    meta = json.loads((page / "meta.json").read_text())
    title = meta["title"].replace("/", "∕").replace("\x00", "")

    conversation_path = page / f"{meta['id']}.json"
    splat_dir = page / f"{meta['id']}.splat"
    messages_dir = splat_dir / "messages"

    conversation = json.loads(conversation_path.read_text())
    mapping = conversation["mapping"]
    current = conversation["current_node"]

    # uuid → (stem, ts, role, content_type)
    by_uuid: dict[str, tuple[str, str, str, str]] = {}
    for entry in messages_dir.iterdir():
        if entry.suffix != ".json":
            continue
        # stem: <iso-ts>.<role>.<uuid>.<content_type>; iso-ts has no '.'
        stem = entry.stem
        parts = stem.split(".")
        if len(parts) == 4:
            ts, role, uuid, content_type = parts
            by_uuid[uuid] = (stem, ts, role, content_type)

    rel_to_messages = messages_dir.relative_to(page)

    sections: list[str] = []
    for uuid in walk_to_current(mapping, current):
        record = by_uuid.get(uuid)
        if record is None:
            continue
        stem, ts, role, content_type = record
        md_path = messages_dir / f"{stem}.md"
        if not md_path.exists():
            continue
        time_of_day = ts[11:19]  # 'HH:MM:SS' from '<date>T<HH:MM:SS>,<ns><tz>'
        seq = f"{len(sections):03d}"
        heading_text = f"{seq} · {role} · {time_of_day}"
        if content_type != "text":
            heading_text += f" ({content_type.replace('_', ' ')})"
        link = f"{rel_to_messages}/{stem}.md"
        body = md_path.read_text()
        sections.append(f"# [{heading_text}]({link})\n\n{body.rstrip()}\n")

    out = page / f"{title}.md"
    if out.is_symlink():
        out.unlink()
    out.write_text("\n".join(sections))
    print(f"Rendered {len(sections)} turn(s) → {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
