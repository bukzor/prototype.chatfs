# Devlog: 2026-07-15 -- atomic regeneration design settled: .data/$UUID extraction, staged promotion

## Focus

Reworked `todo.kb/2026-07-13-000-Atomic-chat-dir-regeneration-...` from the
ground up. The prior (v2, 2026-07-14) design was found flawed on inspection;
a fresh problem inventory and design session produced a different shape,
now persisted where it belongs: layout and flow as `[!TODO]` blocks in
`design.kb/040-design.kb/` (five docs), mechanism as a code sketch
(`chatfs_atomic.py`, imported nowhere yet), and the task file reduced to
problem + pointers + steps.

## Problem inventory (independent of any proposed fix)

One shape in five places -- destroy-then-rebuild with readers unprotected:

- path_render purges all derived content, then rebuilds over seconds;
  `chat.md` additionally streams incrementally into place.
- `place_meta` truncate-overwrites `meta.json` (an *input* -- partial JSON
  breaks every downstream verb).
- `capture()` deletes the prior capture, then runs the flakiest stage
  (browser). Worst instance: captured data is not locally re-derivable.
- `_purge_view_symlinks` unlinks before re-place -- a crash makes the chat
  vanish from every view.

Checked and not problems: stale `conversation.splat/` contamination (splat
clears its own output); the `messages/` move-up (same-fs rename).

## Decisions

### v2 rejected on its own success criteria

Per-artifact swaps (`messages/`, `conversations/`, `chat.md` independently)
can't satisfy the requirement's "old complete state or new complete state":
`chat.md` hyperlinks into `messages/` by stem, so mixed sets are visible to
all readers. Its two-rename dir swap has an ENOENT window on every run and
an unbounded broken window after a kill between renames. Its
`atomic_write(data)` buffered in-progress output in memory -- user
requirement is the opposite: spool to disk, adjacent to the destination,
so a crash leaves the bytes inspectable.

### The staged unit is the whole chat dir; the layout moves to make that true

The only obstacle to staging `.chat/$UUID/` whole was `.data/` (input)
living inside it. Extracted to a parallel tree: `.data/$UUID/` captured,
`.chat/$UUID/` 100% derived with a `.data` symlink back
(`../../.data/$UUID` -- same relative target valid from the scratch dir).
One `staged()` call per regeneration, splat and render both inside it;
whole-derived-surface atomicity for every reader, lockless humans included.

Alternative rejected: keep `.data` inside, make root `messages/` etc.
symlinks into a promoted `.data/conversation.splat/`. Disqualifier:
`grep -r`/`rg` don't follow encountered dir symlinks -- chats go dark to
recursive search, the primary Unix-tools use case. (Corollary win of the
chosen layout: `.data` *as* a symlink takes `cdp.jsonl` out of recursive
grep, which it pollutes today.)

Parallel-tree naming (`.data/$UUID`, user's call) over suffix-sibling
(`.chat/$UUID.data`): data-class encoded structurally, not in a string
suffix; retention policy becomes a path; `.chat/` stays homogeneous.

### Mechanism is code, not prose

`chatfs_atomic.py` -- design-sketch module, imported nowhere (user call:
an unwired skeleton beats prose spec; prose-spec'd mechanism was v2's
failure mode). Three public names: `read_locked`/`write_locked` (flock on
a stable anchor dir -- `.data/$UUID/`, never renamed; kernel releases on
crash), `staged` (entry-time recovery, yield reserved-nonexistent scratch,
promote on success, rotate to `.fail` on exception), over a `promote`
kernel (files/symlinks: `os.replace`; dirs: `renameat2(RENAME_EXCHANGE)`
with two-rename-via-`.old` fallback). Crash and exception converge:
failed attempts always end at `.fail` (latest-wins, cleared by next
success); every fingerprint a kill can leave is healed on next entry.

### Doc-driven demarcation

Five `[!TODO]` blocks: `chat-as-directory.md` (normative layout),
`deterministic-regeneration.md` (promotion supersedes advance purge;
purity guarantee unchanged; symlink cleanup inverts to place-then-purge),
plus pointer-TODOs in `captured-vs-derived.md`, `pipeline-implications.md`,
`view-symlink.md` (the dir-symlink itself dangles pre-first-render -- kept
deliberately as the "not yet synced" signal).

## Principles surfaced

- In design sessions, current code shape is data, not constraint --
  mid-session realignment happened because the assistant kept wrapping the
  existing splat output shape in API glue instead of restructuring.
- Task files hold problem + pointers + steps; design lives in design.kb
  `[!TODO]`s; mechanism lives in (sketch) code.

## Loose ends

- `chatfs_atomic.py` got fixes for basedpyright's 4 warnings
  (`Generator` annotations, `cast` for the ctypes return) but the re-run
  was skipped at wrap-up; the task's step-1 test gate covers it.
- `uv run basedpyright` is broken in this worktree: missing distribution
  `../basedpyright-as-pyright` (sibling-worktree path dependency).
  `uvx basedpyright` used as a stopgap.
- `Skill(llm-subtask)` references `bin/session-end`, which doesn't exist
  in the skill's `bin/`.
