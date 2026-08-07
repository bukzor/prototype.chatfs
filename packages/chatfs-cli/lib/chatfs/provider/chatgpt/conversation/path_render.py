#!/usr/bin/env python3
"""Render a chatgpt conversation from already-captured artifacts.

Usage:
    python -m chatfs.provider.chatgpt.conversation.path_render <path-to-chat-dir-or-inside>

Prerequisites in the resolved chat dir's `.data/$UUID/` twin:
    meta.json           — placed by index splat or url browse
    conversation.json   — output of conversation pluck

Builds the entire derived surface (messages/, chat.md, the .data
inspection symlink) in a staged scratch sibling and atomically promotes
it over chat_dir in one swap -- readers see the old complete chat dir
or the new one, never partial or mixed. See chatfs.shell.atomic's module
docstring for the mechanism; `staged` takes data_dir's write lock
itself (from chatfs.shell.locks, reentrant), so no separate lock
acquisition is needed here.

Splat runs via the external `chatgpt-splat` command (packages/
bukzor.chatgpt-export) rather than an in-tree module — that package has
its own pyproject.toml, test suite, and typesafety tests, so it keeps
its independent package identity instead of folding into this
incubator (see the module-shape-refactor todo for the full rationale).
Render runs as a subprocess (`python -m
chatfs.provider.chatgpt.conversation.render`), not an in-process
import, deliberately -- see `design.kb/040-design.kb/driver-model.md`:
every pipeline-stage boundary stays crossable only through argv/stdio.
"""
from chatfs.layout import data_dir_of
from chatfs.paths import INCUBATOR_ROOT
from chatfs.shell import sh as chatfs_sh
from chatfs.shell.atomic import staged
from chatfs.shell.place import link_data_dir, resolve_chat_dir


def main() -> None:
    import sys

    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path-to-chat-dir-or-inside>", file=sys.stderr)
        sys.exit(2)

    chat_dir = resolve_chat_dir(sys.argv[1])
    uuid = chat_dir.name
    data_dir = data_dir_of(chat_dir)
    meta_path = data_dir / "meta.json"
    assert meta_path.exists(), f"missing meta.json: run index browse first ({meta_path})"
    conversation = data_dir / "conversation.json"
    assert conversation.exists(), (
        f"missing conversation.json: run conversation browse first ({conversation})"
    )

    with staged(chat_dir, anchor=data_dir) as tmp:
        tmp.mkdir(parents=True)
        link_data_dir(tmp, uuid)

        print(f"Splatting {conversation} ...", file=sys.stderr)
        _ = chatfs_sh.run(["chatgpt-splat", str(conversation), str(tmp)])

        out = tmp / "chat.md"
        print(f"Rendering {tmp} → chat.md ...", file=sys.stderr)
        with out.open("wb") as f:
            _ = chatfs_sh.run(
                [
                    sys.executable,
                    "-m",
                    "chatfs.provider.chatgpt.conversation.render",
                    str(tmp),
                ],
                cwd=INCUBATOR_ROOT,
                stdout=f,
            )


if __name__ == "__main__":
    main()
