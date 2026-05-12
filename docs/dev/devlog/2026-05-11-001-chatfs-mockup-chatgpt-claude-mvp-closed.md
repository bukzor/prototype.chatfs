# 2026-05-11: chatfs-mockup-chatgpt — claude MVP closed

## Focus

Land `chatfs_claude_conversation_path_render.py`, the last MVP rung in
the claude parity ladder: single chat URL → `chat.md` for linear
chats.

## What Happened

**Mechanical mirror of the chatgpt orchestrator.** The shape matches
`chatfs_chatgpt_conversation_path_render.py` line-for-line in
structure: `purge_non_captured` (allowlist `{".data"}`), invoke splat,
move splat outputs up, invoke render to `chat.md`.

Two provider-shaped deltas worth naming:

1. **Splat is a sibling script, not a PATH console script.** Chatgpt
   side calls `chatgpt-splat` from `bukzor.chatgpt_export.splat`
   (installed in `.venv/bin/`). Claude side calls
   `chatfs_claude_conversation_splat.py` via
   `Path(__file__).parent`. This is a leak the lib-extraction work
   will tidy: orchestrators should not need to know whether the
   helper is on `$PATH` or a sibling file.
2. **Splat output is `messages/` only — no `conversations/`.** Claude
   branch-symlink emission isn't on the ladder yet (next rung). The
   move loop iterates `splat.iterdir()` so it remains correct when
   `conversations/` lands later.

**Verified against the captured test chat** at `chatfs.demo/claude/
.chat/b0f46746-…/` (12 messages, 1 thinking-only / 11 with text). Two
runs produced byte-identical `chat.md` (md5
`251c88f634…970950701`), confirming determinism per
`docs/dev/adr/2026-04-29-000-no-freshness-caches.md`.

## Lessons

**The path_render shape is provider-shaped, not provider-specific.**
After mirroring it for a second provider, the only real variation is
how the splat helper is invoked (`$PATH` vs sibling). Everything else
— allowlist, move loop, render hand-off — survives identical. When
the parity ladder reaches the lib-extraction rung, `path_render` is a
strong candidate for the shared core; the per-provider piece reduces
to a one-line "how to invoke splat".

**Idempotence falls out of purge + rm-rf splat.** No flags to plumb,
no freshness checks; the second run wipes derived state and rebuilds
it. The chatgpt side already validated this pattern at scale (188-
message rerender, byte-stable). Replicating it on claude with no
adjustments is the strongest signal yet that determinism is the right
discipline.

## Next Session

- **Browse-side automation:** `chatfs_claude_conversation_url_browse.py`
  and `chatfs_claude_index_browse.sh` — the entry points that match
  the chatgpt side's user-facing surface. Solving "wait until
  `has_more=false`" on `/recents` is the open question.
- **Branches in splat:** emit `conversations/<branch>.md` symlinks
  per leaf. The render side already groups dead branches as nested
  asides; the symlinks make each branch independently navigable from
  the chat dir root.
- **Rich content blocks:** thinking, tool_use, tool_result render
  paths (proposed formats in `todo.md`). The capture exercises all
  four block types so this is shovel-ready.
