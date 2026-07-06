#!/usr/bin/env python3
"""Splat an AI Studio conversation JSON into a `messages/` directory.

Input: path to conversation.json — chatfs_aistudio_conversation_massage_json's
named projection of the plucked ResolveDriveResource body.

Output: `<src>.splat/messages/<basename>.{json,md}` per turn, one per
`prompt.chunkedPrompt.chunks[]` entry. The .json carries the raw turn
object; the .md carries the rendered content. Mirrors
chatfs_claude_conversation_splat's directory shape so the two providers
read side-by-side.

Scope: user prompts and model answers pass their text through; model
`thought` turns render as a collapsible `<details type="thinking">`
section (the `type` attribute matches the claude side, keeping reasoning
greppable across providers). The raw turn stays in the .json regardless.

Turns carry a `createTime` but no unique id, and user/thought turns can
share a timestamp, so basenames lead with the turn index (zero-padded,
document order) rather than claude's `{ts}.{uuid}`.
"""
import json
import re
import shutil
import sys
from pathlib import Path

import chatfs_json
from chatfs_aistudio_types import Conversation, Turn, is_conversation


def turns_of(doc: Conversation) -> list[Turn]:
    return doc["prompt"]["chunkedPrompt"]["chunks"]


def turn_kind(turn: Turn) -> str:
    """One of user | answer | thought; raises on an unclassifiable turn.

    Roles are a closed set in the captured payloads; a model turn that is
    neither answer nor thought is a parser gap, not a soft case.
    """
    role = turn["role"]
    if role == "user":
        return "user"
    elif role == "model":
        if turn.get("isThought") == 1:
            return "thought"
        elif turn.get("finishReason") == 1:
            return "answer"
        else:
            raise AssertionError(("model turn is neither thought nor answer", turn))
    else:
        raise AssertionError(("unexpected turn role", role))


def thought_label(text: str) -> str:
    """The leading `**bold**` header AI Studio gives each reasoning turn."""
    match = re.match(r"\*\*(.+?)\*\*", text.strip())
    return match.group(1) if match else "Thinking"


def strip_leading_header(text: str, label: str) -> str:
    """Drop a leading `**label**` line when it duplicates the disclosure title.

    AI Studio repeats the header in the body, so the lifted `<summary>`
    would show it twice. Only strip when the body's first line is exactly
    `**label**`, leaving a `**bold**` that merely opens a sentence intact.
    """
    first, _, rest = text.partition("\n")
    if first.strip() == f"**{label}**":
        return rest.lstrip("\n")
    else:
        return text


def render_details(kind: str, icon: str, label: str, body: str) -> str:
    """Wrap non-answer content in a collapsible `<details>`, tagged for grep.

    `type="{kind}"` mirrors the claude splat so a single
    `grep 'type="thinking"'` spans both providers.
    """
    return (
        f'<details type="{kind}"><summary>{icon} {label}</summary>'
        f"\n\n{body}\n\n</details>"
    )


def render_turn(turn: Turn, kind: str) -> str:
    """Render one turn to markdown by kind; thoughts collapse, the rest pass through."""
    text = turn["text"].strip()
    if kind == "thought":
        label = thought_label(text)
        return render_details("thinking", "💭", label, strip_leading_header(text, label))
    else:
        return text


def basename_for(index: int, kind: str) -> str:
    """`{index}.{role}` (+`.thought`), zero-padded so document order sorts."""
    role = "user" if kind == "user" else "model"
    suffix = ".thought" if kind == "thought" else ""
    return f"{index:03d}.{role}{suffix}"


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <conversation.json>", file=sys.stderr)
        sys.exit(1)

    src = Path(sys.argv[1])
    parsed = chatfs_json.loads(src.read_text())
    assert is_conversation(parsed), parsed
    turns = turns_of(parsed)

    base_dir = src.with_suffix(".splat")
    messages_dir = base_dir / "messages"
    if base_dir.exists():
        shutil.rmtree(base_dir)
    messages_dir.mkdir(parents=True)

    rendered_count = 0
    for index, turn in enumerate(turns):
        kind = turn_kind(turn)
        basename = basename_for(index, kind)
        _ = (messages_dir / f"{basename}.json").write_text(
            json.dumps(turn, indent=2, ensure_ascii=False) + "\n"
        )
        text = render_turn(turn, kind)
        if text:
            _ = (messages_dir / f"{basename}.md").write_text(text + "\n")
            rendered_count += 1

    print(
        f"wrote {len(turns)} turn(s), {rendered_count} with rendered content, to {base_dir}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
