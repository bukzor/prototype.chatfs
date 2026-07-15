---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    "@value": 5.0
    rationale: >
      Design settled 2026-07-15; the normative surface is written down
      (layout and flow as design.kb !TODO blocks, mechanism as the
      chatfs_atomic.py sketch), so what remains is wiring and tests.
      Scope grew from the original 2.0 estimate: not just the render
      flow but a layout migration (.data/$UUID extraction) across three
      providers, a splat output-dir argument, the capture/meta.json
      ride-alongs, and crash-matrix tests.
    confidence: confident
  benefit-2w:
    "@value": 0.5
    rationale: >
      No live consumer races today (regeneration is human-driven, single
      user), but this is a hard precondition for the fuser integration --
      requirement 030/atomic-cache-updates's kill-mid-sync test must pass
      before a mount serves these trees. Doing it pre-promotion means the
      code graduates already-compliant.
    confidence: tentative
---

# Atomic chat-dir regeneration -- stage and promote, never rewrite in place

**Priority:** First -- top of the tactical list as of 2026-07-13 (user call,
planning session). Precondition for fuser-vfs integration; should land
before or with the module-shape refactor so promoted code is born compliant.
**Context:** `docs/dev/design.kb/030-requirements.kb/atomic-cache-updates.md`
(verification: kill a sync mid-flight; the mount continues serving the
previous content without errors) and
`docs/dev/design.kb/040-design.kb/work-enqueueing-model.md`
(staging -> atomic rename; last-known-good untouched).

## Problem

One shape in five places: **destroy-then-rebuild with readers unprotected.**

- `chatfs_*_conversation_path_render.py` purges all derived content
  (`messages/`, `conversations/`, `chat.md`), then rebuilds over seconds.
  A crash destroys last-known-good; readers see empty/partial states on
  every run (`chat.md` streams incrementally from render's stdout).
- `place_meta` truncate-overwrites `meta.json` in place -- a crash leaves
  partial JSON, and it's an *input*, so downstream verbs break on it.
- `capture()` deletes `cdp.jsonl`/`conversation.json`, then runs the most
  failure-prone stage (browser automation). A failed browse destroys the
  prior capture -- the one artifact class that is not locally
  re-derivable.
- `_purge_view_symlinks` unlinks before `place_meta` re-places -- a crash
  makes the chat vanish from every view until the next index splat.

## Design (settled 2026-07-15)

The design lives in its normative homes, not here:

- **Layout:** `design.kb/040-design.kb/chat-as-directory.md` !TODO --
  captured exhaust moves to a parallel `.data/$UUID/` tree;
  `.chat/$UUID/` becomes 100% derived (with a `.data` inspection
  symlink) and is THE staged unit, swapped whole. Sub-kb consequences in
  `captured-vs-derived.md`, `pipeline-implications.md`,
  `view-symlink.md` !TODOs.
- **Flow:** `design.kb/040-design.kb/deterministic-regeneration.md`
  !TODO -- supersession by atomic promotion replaces advance purge;
  failed attempts preserved as `.fail`; view-symlink cleanup inverts to
  place-then-purge.
- **Mechanism:** `chatfs_atomic.py` -- a design-sketch module, imported
  nowhere yet: three public names (`read_locked`/`write_locked`/
  `staged`) over a private `_promote` kernel. Its docstrings carry the
  contracts (locking, sibling naming, `.fail` lifecycle, crash recovery,
  fsync out of scope); its bodies are the spec.

**Alternatives rejected:**

- `redo` (2026-07-14): its `foo.d.do` directory-target recipe is this
  exact pattern, but it isn't packaged as a library and would become a
  runtime dependency of shipped `chatfs-cli`, which its packaging can't
  support cleanly.
- Per-artifact helpers, v2 (2026-07-14, superseded 2026-07-15):
  in-memory `atomic_write(data)` plus `atomic_replace_dir` swapping
  `messages/`, `conversations/`, `chat.md` independently. Rejected on a
  ground-up problem inventory: mixed old/new artifact sets visible to
  all readers (chat.md hyperlinks into messages/ by stem); an ENOENT
  window in its two-rename swap on every run; a crash between renames
  leaves the tree broken until some later run heals it; in-progress
  output buffered in memory instead of spooled to disk.

## Implementation Steps

- [ ] `chatfs_atomic.py`: unit tests against the sketch -- crash matrix
      (kill during populate / between `_swap_via_old` renames / before
      `.old` cleanup / stale `.tmp` on entry), file<->dir type change
      across versions, `.fail` lifecycle (latest-wins, cleared on
      success), `_exchange` fallback path
- [ ] Layout migration to `.data/$UUID`: `chatfs_layout.py`
      (`data_dir_for`, `place_meta`, `capture`, `resolve_chat_dir`) and
      the three provider layouts; `.data` symlink inside the chat dir
- [ ] Splat scripts gain an output-dir argument (today they derive
      `<src>.splat` themselves)
- [ ] Rewrite the three `chatfs_*_conversation_path_render.py` to the
      one-staged-call shape (see `chatfs_atomic.py` module docstring);
      delete `purge_non_captured` and the move-up loop
- [ ] Ride-alongs: `capture()` outputs and `meta.json` through `staged`;
      view-symlink place-then-purge inversion
- [ ] Docs: unwrap the !TODO blocks in `chat-as-directory.md`,
      `captured-vs-derived.md`, `pipeline-implications.md`,
      `view-symlink.md`, `deterministic-regeneration.md`
- [ ] Kill-mid-flight test per the requirement's verification, killing
      at each stage boundary and inside the promote

## Success Criteria

- [ ] Requirement verification passes for ALL readers -- no lock needed
      to observe only old-complete or new-complete chat dirs
- [ ] No verb destroys data before its replacement is secured --
      including `capture()` (a failed browse leaves the prior capture
      intact)
- [ ] A crashed run's partial output is preserved on disk for
      inspection; the next run self-heals with no manual cleanup
- [ ] Full test suite + basedpyright clean

## Notes

Created 2026-07-13 during the promotion/integration planning session, from
the observation that requirement `atomic-cache-updates` had no owning task.
Re-homes with the code when the incubator graduates to `packages/`.

Design v2 (2026-07-14) superseded 2026-07-15 after a ground-up problem
inventory and design session; see Alternatives rejected.
