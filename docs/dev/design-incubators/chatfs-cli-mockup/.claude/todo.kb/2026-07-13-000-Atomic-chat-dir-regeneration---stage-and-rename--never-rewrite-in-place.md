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

## Coordination note (2026-07-17, from the parallel locks/design session)

Commit `bf9a443` landed `chatfs_locks.py` — a process-tree-reentrant
lock table (`registry` + `__CHATFS_LOCKS` env var) that supersedes
`chatfs_atomic`'s `read_locked`/`write_locked`. For the step-4/5 wiring
below:

- **Import locks from `chatfs_locks`, not `chatfs_atomic`.**
  `chatfs_atomic`'s copies are non-reentrant: a write-locked
  orchestrator whose subprocess locks the same anchor self-deadlocks
  (flock is per-OFD), and re-flocking a held fd *converts* the lock
  (LOCK_SH under EX silently downgrades). `chatfs_locks` borrows the
  inherited fd instead (dev/ino probe, no syscall).
- **Spawn lock-holding children via `chatfs_locks.run()`** — bare
  `subprocess.run` drops the fds (PEP 446 non-inheritable default).
  Superseded 2026-07-17 (user call): production call sites now use
  `chatfs_sh.run` instead (`close_fds=False`, plus lock fds opened
  inheritable in `chatfs_locks._locked`), so the whole fd table
  crosses exec, not just a curated `pass_fds` list; `chatfs_locks.run`
  remains for test/orchestration use. All 13 real call sites
  (`run_pluck`, `capture()`'s har-browse, every provider's
  path_render/path_browse/url_render/url_browse) wired -- see
  `2026-07-17-000-chatfs-locks--...md`, now closed.
- `chatfs_atomic`'s lock helpers + its 3 `DescribeLocking` tests are
  slated to migrate into `chatfs_locks`; deliberately deferred so this
  session's in-flight work doesn't break. Tracked in
  `2026-07-17-000-chatfs-locks--...md` — take it if convenient,
  otherwise it lands after you do. Done 2026-07-17.
- Environment landmine, already defused: a stale `__pycache__` pyc had
  `read_locked` compiled as `LOCK_EX` (same-second, same-length edit —
  mtime+size validation can never catch it). If phantom lock-test
  failures appear, `rm -r __pycache__` first.

## Implementation Steps

- [x] `chatfs_atomic.py`: unit tests against the sketch -- crash matrix
      (kill during populate / between `_swap_via_old` renames / before
      `.old` cleanup / stale `.tmp` on entry), file<->dir type change
      across versions, `.fail` lifecycle (latest-wins, cleared on
      success), `_exchange` fallback path -- done 2026-07-16:
      `chatfs_atomic_test.py`, 18 tests (incl. locking semantics);
      pytest 18/18, basedpyright 0/0/0 (closes the skipped-re-run
      loose end from devlog 2026-07-15-000)
- [x] Layout migration to `.data/$UUID`: `chatfs_layout.py`
      (`data_dir_for`, `place_meta`, `capture`, `resolve_chat_dir`) and
      the three provider layouts; `.data` symlink inside the chat dir --
      done 2026-07-17: `data_dir_for` now returns `root/.data/$uuid`
      (moved out from under chat_dir); new `data_dir_of(chat_dir)` and
      `link_data_dir(dst, uuid)` helpers (the latter's fixed relative
      target, `../../.data/$UUID`, is valid unchanged from both the
      final chat_dir and a same-depth staged scratch sibling -- tested
      directly). `resolve_chat_dir` rewritten to climb by
      `p.parent.name` instead of `is_dir()`, so a not-yet-rendered
      (nonexistent) chat_dir or a dangling view symlink resolves
      correctly instead of requiring existence -- verified against the
      old algorithm (4 tests fail without the fix). Caught and fixed a
      second latent bug along the way: `_purge_view_symlinks` swept by
      "target string contains uuid", which also matched the new
      `.chat/$UUID/.data` inspection symlink -- a re-`place_meta` after
      a render would have deleted it (verified: fails without the fix).
      `capture`/`place_meta` no longer touch `.chat/$UUID/` at all
      (may not exist yet); the three `path_render.py`'s
      `purge_non_captured` simplified to an unconditional reset (no
      more `.data` allowlist, since nothing under `.chat/$UUID/` is
      captured anymore) plus an explicit `link_data_dir` call --
      interim shape, still purge-then-rebuild-in-place (step 4 replaces
      this with `staged()`). All `chat_dir / DATA_DIR_NAME / ...`
      call sites (path_browse, path_render, the bare render leaves,
      url_render) switched to `data_dir_of`/`data_dir_for`; stale
      docstrings referencing the old nested path fixed throughout.
      Hand-verified end-to-end against the real claude scripts: index
      splat -> dangling view symlink -> path_render through that
      dangling path -> chat.md correct, `.data` symlink correct,
      re-render idempotent, re-place_meta (title change) preserves the
      `.data` inspection symlink and moves the view symlink. pytest
      62/62 (16 new/updated in `chatfs_layout_test.py`), basedpyright
      0/0/0 (chatfs_locks* excluded -- parallel session's work, out of
      scope here).
- [x] Splat scripts gain an output-dir argument (today they derive
      `<src>.splat` themselves) -- done 2026-07-17: optional 2nd argv on
      all three (`chatfs_claude_conversation_splat.py`,
      `chatfs_aistudio_conversation_splat.py`,
      `bukzor.chatgpt_export.splat`); default (`<src>.splat`) unchanged
      for bare single-arg invocation. Cleanup scoped to the owned
      subdirs (`messages/`, `conversations/`) rather than the whole
      output-dir, so an explicit output-dir's sibling content (e.g. a
      caller-placed `.data` symlink) survives -- needed for step 4's
      one-staged-scratch shape. Smoke-tested by hand (all three,
      default + explicit-dir + sibling-preservation); pytest 50/50,
      basedpyright 0/0/0 both packages.
- [x] Rewrite the three `chatfs_*_conversation_path_render.py` to the
      one-staged-call shape (see `chatfs_atomic.py` module docstring);
      delete `purge_non_captured` and the move-up loop -- done
      2026-07-17: each now wraps `write_locked(data_dir): with
      staged(chat_dir) as tmp: ...` around `tmp.mkdir(parents=True)` +
      `link_data_dir(tmp, uuid)` + splat (writing straight into `tmp`
      via its new output-dir arg, no `.splat`/move-up/rmdir) + render
      (stdout piped to `tmp/chat.md`); `purge_non_captured` and the
      move-up loop deleted entirely. `write_locked` imported from
      `chatfs_locks` (not `chatfs_atomic`) per the parallel locks
      session's coordination note above, so this script's own lock
      acquisition is reentrant-safe once a future ancestor (step 5)
      holds the same anchor across a subprocess boundary. Found and
      fixed a real bug surfaced by the rewrite: the claude/chatgpt bare
      `render.py` leaves had been switched to `data_dir_of(chat_dir)`
      in step 2, which breaks when path_render invokes them against
      the staged scratch (`.chat/.$UUID.tmp/`, whose `.name` isn't the
      bare uuid) -- reverted those two back to reading via
      `chat_dir/.data` (the inspection symlink, already correctly
      targeted by `link_data_dir`'s explicit-uuid parameter regardless
      of the containing dir's name); aistudio's render.py leaf was
      unaffected (never reads `.data` at all). Hand-verified end to
      end for all three providers (first render through a dangling
      view path, idempotent re-render, self-heal from a hand-crafted
      abandoned scratch, and a genuine forced failure -- reader-visible
      `chat.md` unchanged, failed attempt preserved as `.fail`,
      `.fail` cleared on the next success). No new automated test file
      added for the orchestration scripts themselves, matching this
      repo's existing convention (no CLI orchestrator here has direct
      unit tests, only its constituent pure functions) -- the
      mechanism is already covered by `chatfs_atomic_test.py`'s 18
      tests, and a real process-kill harness is explicitly the
      separate "Kill-mid-flight test" item below, not this one. pytest
      62/62, basedpyright 0/0/0 (chatfs_locks* excluded, out of scope).
- [x] Ride-alongs: `capture()` outputs and `meta.json` through `staged`;
      view-symlink place-then-purge inversion -- done 2026-07-18:
      `capture()` now wraps its two outputs (`cdp.jsonl`,
      `conversation_filename`) in one outer `chatfs_locks.write_locked
      (data_dir)` spanning two inner `chatfs_atomic.staged()` calls, per
      the module docstring's own worked example ("capture()'s two
      files"); a failed browse (the most failure-prone stage, and the
      one artifact class that isn't locally re-derivable) now leaves
      the prior `cdp.jsonl` untouched instead of destroying it, and a
      failed pluck leaves the prior `conversation.json` untouched even
      though the new `cdp.jsonl` is kept. `place_meta` gained the same
      shape: `meta.json` and the view symlink each go through `staged`,
      and `_purge_view_symlinks` gained a `keep` param so the fresh
      symlink can be placed *before* the stale one(s) are swept
      (place-then-purge, per `deterministic-regeneration.md`'s
      `[!TODO]` block) without the purge immediately undoing the
      placement it's supposed to follow -- a crash between the two
      leaves the chat briefly visible under two paths, never invisible
      from every view. 5 new tests in `chatfs_layout_test.py`
      (`DescribeCapture` + one in `DescribePlaceMeta`), each
      hand-mutation-tested (reverted the fix, confirmed the new test
      fails, restored). pytest 91/91, basedpyright 0/0/0.
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
