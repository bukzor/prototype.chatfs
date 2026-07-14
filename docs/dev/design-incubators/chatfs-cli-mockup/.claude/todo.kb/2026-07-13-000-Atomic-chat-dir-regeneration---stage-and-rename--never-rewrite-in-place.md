---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    "@value": 2.0
    rationale: >
      Mechanical: the staging + swap design is settled (2026-07-14, see
      Proposed Solution) down to the helper function bodies. path_render
      already builds splat output in a staging-like dir
      (.data/conversation.splat/) before moving it; the change is to route
      the whole regenerated surface (messages/, conversations/, chat.md)
      through two small shared helpers instead of purge-then-rebuild.
    confidence: confident
  benefit-2w:
    "@value": 0.5
    rationale: >
      No live consumer races today (regeneration is human-driven, single
      user), but this is a hard precondition for the fuser integration —
      requirement 030/atomic-cache-updates's kill-mid-sync test must pass
      before a mount serves these trees. Doing it pre-promotion means the
      code graduates already-compliant.
    confidence: tentative
---

# Atomic chat-dir regeneration — stage and rename, never rewrite in place

**Priority:** First — top of the tactical list as of 2026-07-13 (user call,
planning session). Precondition for fuser-vfs integration; should land
before or with the module-shape refactor so promoted code is born compliant.
**Complexity:** Low-Medium
**Context:** `docs/dev/design.kb/030-requirements.kb/atomic-cache-updates.md`
("Readers always see either the old complete state or the new complete
state, never a partial update. Verification: kill a sync mid-flight; the
mount continues serving the previous content without errors.") See also
`docs/dev/design.kb/040-design.kb/work-enqueueing-model.md` (staging/<jobid>
→ atomic rename) and this incubator's
`design.kb/040-design.kb/deterministic-regeneration.md`.

## Problem Statement

The requirement is violated today: regeneration mutates the live chat dir
in place. A reader (today: a human mid-`ls`; tomorrow: the FUSE mount) can
observe a half-built chat dir, and a sync killed mid-flight leaves the
previous content destroyed rather than intact.

## Current Situation

`chatfs_*_conversation_path_render.py` purges non-captured contents of the
chat dir (allowlist `{".data"}`), then splats into `.data/conversation.splat/`,
moves `messages/` and `conversations/` up into the chat-dir root, and
redirects render stdout into `chat.md`. Between the purge and the last move,
the chat dir is incomplete; a crash strands it that way. Index splat's
view-symlink purge/replace has the same shape in miniature.

## Proposed Solution

`redo` was considered (its `foo.d.do` directory-target recipe in
`~/.claude/design-rules.kb/redo.kb/` is this exact pattern, already used
in-repo for `docs/dev/aistudio-schema/bundles.do`) and rejected for this
use: it isn't packaged as a library, only a standalone binary, and it
would become a runtime dependency of shipped `chatfs-cli` (not dev-only
tooling like its `aistudio-schema` usage), which its packaging can't
support cleanly. Decided 2026-07-14. Its atomicity primitive — build to a
sibling tmp path, `rename(2)` into place — is a single OS syscall
guarantee, not something redo owns; use it directly via `os.replace`.

Per-artifact swap, not whole-chat-dir: `.data/` (captured exhaust) is
input, never a swap target and never touched. Only the derived contents
(`messages/`, `conversations/`, `chat.md`) each swap independently. This
sidesteps the whole-dir-vs-per-artifact question entirely — there is no
single rename covering `.data/` plus derived output.

Two shared helpers, alongside `chatfs_layout.py`/`chatfs_json.py`
(new module, working name `chatfs_atomic.py`):

- `atomic_write(target, data)` — write to `target.tmp`, `os.replace(tmp,
  target)`. Single rename, no gap. Used for `chat.md`.
- `atomic_replace_dir(target)` — context manager: caller populates a
  yielded `target.tmp` dir; on clean exit, swap via `target.old` (two
  renames: `target→old`, `tmp→target`) then remove `old`; on exception,
  remove `tmp` and leave `target` untouched. Used for `messages/`,
  `conversations/`.

**Crash-recovery subtlety (design it in, don't discover it later):**
`atomic_replace_dir`'s two-rename swap has a window a `kill -9` can land
in — no `except` clause runs for SIGKILL. If that happens, `target` is
missing and `old` holds the real prior content until something notices.
Fix: on entry, if `target` is absent but `old` exists, that's the
fingerprint of an interrupted swap — rename `old` back to `target` before
proceeding. `atomic_write`'s single rename has no equivalent gap.

## Implementation Steps

- [ ] Add `chatfs_atomic.py` with `atomic_write` and `atomic_replace_dir`
      (including the crash-recovery check), unit-tested directly:
      interrupted-populate leaves `target` untouched; interrupted-swap
      (manually placed `.old` with no `target`) self-heals on next call;
      stale leftover `.tmp` is cleared on entry.
- [ ] Rework the shared path-render flow (`chatfs_*_conversation_path_render.py`)
      to call the helpers instead of `purge_non_captured` + in-place
      writes/moves.
- [ ] Same treatment for index splat's view-symlink replacement (purge +
      re-place is a smaller window, but the same in-place mutation).
- [ ] Tests: kill-mid-regeneration leaves the prior complete state
      readable; successful regeneration is observable only as complete.

## Success Criteria

- [ ] Requirement doc's verification passes: kill regeneration mid-flight
      at any point (including between `atomic_replace_dir`'s two renames);
      the previous complete chat dir contents still serve.
- [ ] No pipeline stage rewrites a live derived artifact in place.
- [ ] A run started right after an interrupted swap self-heals (recovers
      `old`→`target`) before regenerating, no manual cleanup needed.
- [ ] Full test suite + basedpyright clean.

## Notes

Created 2026-07-13 during the promotion/integration planning session, from
the observation that requirement `atomic-cache-updates` had no owning task.
Re-homes with the code when the incubator graduates to `packages/`
(per the same session's decision: unclosed todos move with the code).

Design settled 2026-07-14: `redo` considered and rejected (packaging isn't
library-friendly enough for a runtime dependency of shipped `chatfs-cli`);
hand-rolled `chatfs_atomic.py` helpers instead, same underlying primitive
(sibling tmp + `rename(2)`) without the dependency. See Proposed Solution.
