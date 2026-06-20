#!/usr/bin/env python3
"""Splat an AI Studio prompt JSON into a `messages/` directory.

Input: path to conversation.json (the plucked ResolveDriveResource body,
a JSPB array — positional fields, not keyed objects).

Output: `<src>.splat/messages/<basename>.{json,md}` per turn. The .json
carries the raw turn array; the .md carries the rendered content. Mirrors
chatfs_claude_conversation_splat's directory shape so the two providers
read side-by-side.

Scope: user prompts and model answers pass their text through; model
`thought` turns render as a collapsible `<details type="thinking">`
section (the `type` attribute matches the claude side, keeping reasoning
greppable across providers). The raw turn stays in the .json regardless.

JSPB has no per-turn id or timestamp, so basenames lead with the turn
index (zero-padded, document order) instead of claude's `{ts}.{uuid}`.
"""
import json
import re
import shutil
import sys
from pathlib import Path

# JSPB field indices in the ResolveDriveResource prompt payload.
PROMPT = 0  # body[PROMPT] is the prompt object
TURNS = 13  # prompt[TURNS][0] is the live turn list; [1] is the empty draft

# Field indices within a single turn.
TURN_TEXT = 0
TURN_ROLE = 8  # "user" | "model"
TURN_IS_ANSWER = 16  # 1 on a model answer turn
TURN_IS_THOUGHT = 19  # 1 on a model reasoning turn


def turns_of(doc: list) -> list:
    return doc[PROMPT][TURNS][0]


def turn_kind(turn: list) -> str:
    """One of user | answer | thought; raises on an unclassifiable turn.

    Roles are a closed set in the captured payloads; a model turn that is
    neither answer nor thought is a parser gap, not a soft case.
    """
    role = turn[TURN_ROLE]
    if role == "user":
        return "user"
    elif role == "model":
        if turn[TURN_IS_THOUGHT] == 1:
            return "thought"
        elif turn[TURN_IS_ANSWER] == 1:
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


def render_turn(turn: list, kind: str) -> str:
    """Render one turn to markdown by kind; thoughts collapse, the rest pass through."""
    text = turn[TURN_TEXT]
    assert isinstance(text, str), turn
    text = text.strip()
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
    doc = json.loads(src.read_text())
    turns = turns_of(doc)

    base_dir = src.with_suffix(".splat")
    messages_dir = base_dir / "messages"
    if base_dir.exists():
        shutil.rmtree(base_dir)
    messages_dir.mkdir(parents=True)

    rendered_count = 0
    for index, turn in enumerate(turns):
        kind = turn_kind(turn)
        basename = basename_for(index, kind)
        (messages_dir / f"{basename}.json").write_text(
            json.dumps(turn, indent=2, ensure_ascii=False) + "\n"
        )
        text = render_turn(turn, kind)
        if text:
            (messages_dir / f"{basename}.md").write_text(text + "\n")
            rendered_count += 1

    print(
        f"wrote {len(turns)} turn(s), {rendered_count} with rendered "
        f"content, to {base_dir}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
