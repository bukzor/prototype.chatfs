#!/usr/bin/env python3
"""Render a conversation's mapping into the $TITLE.md placeholder.

Walks `mapping` from root, emitting one section per textual turn. The
live path (root → current_node) renders unprefixed; dead branches off
each fork are blockquoted at depth = how many forks deep they sit
inside, and appear right after the fork point so they read as
quoted-asides between the parent turn and the live continuation.

Each section: a `# [seq · role · time](…)` H1 backref to the atomic
turn-file under $TIMESTAMP.splat/messages/, then the message body.

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


def primary_child(
    children: list[str],
    live_set: set[str],
    mapping: Mapping[str, dict],
) -> str | None:
    """Pick the child to continue inline. Live child wins; else latest."""
    for c in children:
        if c in live_set:
            return c
    if not children:
        return None

    def ct(c: str) -> float:
        m = mapping[c].get("message") or {}
        return m.get("create_time") or 0.0

    return max(children, key=ct)


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
    live_set = set(walk_to_current(mapping, current))

    sections: list[tuple[int, str]] = []

    def render(node_id: str, depth: int) -> None:
        record = by_uuid.get(node_id)
        if record is not None:
            stem, ts, role, content_type = record
            md_path = messages_dir / f"{stem}.md"
            if md_path.exists():
                time_of_day = ts[11:19]  # 'HH:MM:SS' from '<date>T<HH:MM:SS>,<ns><tz>'
                seq = f"{len(sections):03d}"
                heading_text = f"{seq} · {role} · {time_of_day}"
                if content_type != "text":
                    heading_text += f" ({content_type.replace('_', ' ')})"
                link = f"{rel_to_messages}/{stem}.md"
                body = md_path.read_text().rstrip()
                section = f"# [{heading_text}]({link})\n\n{body}\n"
                if depth > 0:
                    prefix = "> " * depth
                    section = "".join(
                        (prefix + line).rstrip() + "\n"
                        for line in section.splitlines()
                    )
                sections.append((depth, section))

        children = list(mapping[node_id].get("children") or [])
        primary = primary_child(children, live_set, mapping)
        for c in children:
            if c == primary:
                continue
            render(c, depth + 1)
        if primary is not None:
            render(primary, depth)

    root = next(nid for nid, m in mapping.items() if m.get("parent") is None)
    render(root, 0)

    out_parts: list[str] = []
    prev_depth = -1
    for depth, body in sections:
        if out_parts:
            if depth > 0 and prev_depth == depth:
                # Same dead branch continuing — separator must stay quoted.
                out_parts.append(("> " * depth).rstrip() + "\n")
            else:
                out_parts.append("\n")
        out_parts.append(body)
        prev_depth = depth

    output = "".join(out_parts)
    out = page / f"{title}.md"
    if out.is_symlink():
        out.unlink()
    out.write_text(output)
    print(f"Rendered {len(sections)} turn(s) → {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
