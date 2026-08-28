#!/usr/bin/env python3
"""Render a claude conversation from already-captured artifacts.

Usage:
    chatfs-provider-claude-conversation-path-render <path-to-chat-dir-or-inside>

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

Splat and render run as subprocesses (`python -m chatfs.provider.claude
.conversation.{splat,render}`), not in-process imports, deliberately —
see `design.kb/040-design.kb/driver-model.md`: every pipeline-stage
boundary stays crossable only through argv/stdio, so the CLI-shaped
calling convention stays exercised (not just theoretically available)
and no subsystem can grow a coupling wider than that peephole. Each
stage is still factored into its own importable, testable function
(`splat.splat`, `render.render_chat_dir`) — just not called that way
from here.
"""
from pathlib import Path

from chatfs.layout import data_dir_of
from chatfs.shell import sh as chatfs_sh
from chatfs.shell.atomic import staged
from chatfs.shell.place import find_view_path, link_data_dir, resolve_chat_dir


def path_render(chat_dir: Path) -> None:
    import sys

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

        chatfs_sh.log(f"Splatting {conversation} ...")
        _ = chatfs_sh.run(
            [
                sys.executable,
                "-m",
                "chatfs.provider.claude.conversation.splat",
                str(conversation),
                str(tmp),
            ],
        )

        out = tmp / "chat.md"
        chatfs_sh.log(f"Rendering {tmp} → chat.md ...")
        with out.open("wb") as f:
            _ = chatfs_sh.run(
                [
                    sys.executable,
                    "-m",
                    "chatfs.provider.claude.conversation.render",
                    str(tmp),
                ],
                stdout=f,
            )


def main() -> None:
    import sys

    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path-to-chat-dir-or-inside>", file=sys.stderr)
        sys.exit(2)

    chat_dir = resolve_chat_dir(sys.argv[1])
    path_render(chat_dir)
    view = find_view_path(chat_dir.name, chat_dir.parent.parent)
    print((view or chat_dir) / "chat.md")


if __name__ == "__main__":
    main()
