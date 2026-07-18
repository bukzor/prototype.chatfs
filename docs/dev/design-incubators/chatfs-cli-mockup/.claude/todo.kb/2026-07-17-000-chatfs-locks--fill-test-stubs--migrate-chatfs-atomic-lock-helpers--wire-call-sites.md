---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    "@value": 1.0
    rationale: >
      Module and 14 of 16 tests landed 2026-07-17 (design session); the
      two deliberately-stubbed subprocess tests landed same day in a
      follow-on session (genuine kernel-block orchestration via
      subprocess.Popen + a two-exec-deep grandchild re-entry). Remaining:
      a mechanical lock-helper migration out of chatfs_atomic (~0.5h, no
      longer coordination-blocked -- the parent task's step 4 already
      targets chatfs_locks) and threading chatfs_locks.run through
      chatfs_layout's subprocess call sites (~0.5h, grows run()'s
      deliberately narrow signature).
    confidence: confident
  benefit-2w:
    "@value": 0.5
    rationale: >
      Locking half of the atomic-regeneration work (parent task
      2026-07-13-000): the integration being wired now can self-deadlock
      through subprocess splat/render without process-tree-reentrant
      locks. Landing this before those call sites multiply keeps the
      import swap a one-liner per site.
    confidence: tentative
---

# chatfs_locks: fill test stubs, migrate chatfs_atomic lock helpers, wire call sites

**Priority:** High within the atomic-regeneration effort — child of
`2026-07-13-000-Atomic-chat-dir-regeneration-...` (the locking half).
**Complexity:** Low-Medium
**Context:** `chatfs_locks.py` module docstring (the normative contract:
lock table, eager env sync, borrowed-vs-owned, no-upgrade). Design
session 2026-07-17; key mechanism facts verified live there: a second
`flock()` on a held OFD *converts* (downgrades) the lock, so borrow
paths must never call flock; a single-entry env var deadlocks on
shadowed re-entry, hence the full lock table in `__CHATFS_LOCKS`.

## Problem Statement

`chatfs_locks.py` (process-tree-reentrant flock over per-chat
`.data/$UUID/` anchors: `__CHATFS_LOCKS='11:r 22:w'` env table,
`registry` as in-process truth) landed with tests 2026-07-17, but is
imported nowhere, two of its tests are stubs, and `chatfs_atomic.py`
still carries the superseded non-reentrant `read_locked`/`write_locked`
— a parallel session is actively integrating chatfs_atomic and may wire
call sites to the old helpers.

## Implementation Steps

- [x] Fill `it_survives_a_grandchild_two_execs_deep` (highest value:
      the only test that exercises re-serializing the table from a
      *borrowed* seeded state rather than owned locks -- child uses
      `chatfs_locks.run` to spawn a grandchild re-entering the same
      anchor) -- done 2026-07-17: extracted the child/grandchild
      scripts to `chatfs_locks_test/child_reenter_w.py` and
      `child_spawns_grandchild.py` (file-per-script instead of
      inline `python -c` strings -- the grandchild-spawning script
      references its sibling file directly rather than embedding a
      second script's source via `repr()`)
- [x] Fill `it_blocks_a_second_writer_from_an_unrelated_process_tree`
      (needs start / observe-blocked-not-crashed / release / observe-
      completion orchestration without racing the assertion) -- done
      2026-07-17: a plain (non-`run()`) `subprocess.Popen` under an
      unrelated tree carries no shared fd, so its `_seed()` warns on
      a dead inherited fd and falls through to a real blocking
      `flock()` against the parent's write lock; `proc.wait(timeout=...)`
      raising `TimeoutExpired` proves genuinely-blocked, not crashed,
      before the parent releases and the child completes
- [x] Migrate: delete `read_locked`/`write_locked`/`_locked` from
      `chatfs_atomic.py`, import from `chatfs_locks` -- done 2026-07-17
      (commit `2ab4096`): the 3 `DescribeLocking` tests were deleted
      rather than moved, since `chatfs_locks_test.py::DescribeAcquisition`
      already covers the same (and in one case strictly more) ground;
      75/75 tests, basedpyright 0/0/0
- [x] Rewrite `chatfs_atomic.py`'s locking-contract docstring
      paragraph: the "cannot take it themselves (self-deadlock)"
      rationale is cured by reentrancy; the surviving reason `staged`
      must not self-lock is *span* (one lock covers multiple staged
      promotions — capture()'s two files, place_meta's
      promote-plus-symlink-sweep — or the single-transition guarantee
      is forfeit) -- done 2026-07-17 (commit `9d2539b`); also fixed the
      "Intended shape" example's missing `chatfs_locks` import and
      pointed `read_locked` references at their new home
- [x] Optional misuse guard (import-direction call deferred from the
      design session): `staged` asserts some `w` entry in
      `chatfs_locks.registry` -- done 2026-07-17 (commit `4ec15ad`),
      but superseded on the spot: an assert only checks the misuse
      after the fact, and re-deriving the old "caller must hold the
      lock" contract showed it was stale (a holdover from
      pre-reentrant flock's self-deadlock hazard, which
      `chatfs_locks`'s borrow semantics already solve). Landed instead
      as `staged(dst, anchor=...)` self-locking `anchor` for its own
      duration -- no assert needed, misuse is structurally impossible.
      Multi-call span (capture()'s two files, place_meta's
      promote-plus-symlink-sweep) still works: an outer
      `write_locked(anchor)` around several `staged()` calls is
      borrowed by each inner call rather than re-acquired. The three
      `path_render.py` call sites lost their manual
      `write_locked(data_dir)` wrap as a result (`staged(chat_dir,
      anchor=data_dir)` covers it); 75/75 tests, basedpyright 0/0/0
- [ ] Route subprocess call sites through `chatfs_locks.run` so lock
      fds survive exec: `run_pluck`, `capture()`'s har-browse, the
      path_render splat/render invocations (as they're rewritten by the
      parent task); grow `run()`'s narrow signature per call site
      (stdin/stdout handles first)

## Open Questions

- ~~Sequencing with the parallel integration session: who lands the
  migration, and does their step-4 wiring target `chatfs_locks` from
  the start?~~ Resolved 2026-07-17: the parent task's step 4 already
  imports `write_locked` from `chatfs_locks`, confirmed live in
  `chatfs_atomic.py`'s absence of any such import and the three
  `path_render.py` scripts' `from chatfs_locks import write_locked`.
  Migration is unblocked; whichever session picks up the remaining
  steps here can proceed without further coordination.

## Success Criteria

- [x] `chatfs_atomic.py` has no flock code; one lock API, in
      `chatfs_locks`
- [x] Zero stub tests; suite green; basedpyright 0/0/0
- [ ] Every subprocess spawn between chatfs verbs carries the lock
      table (audit: no bare `subprocess.run` between them)

## Notes

Created 2026-07-17 by a session-end fork of the lock-design session;
`chatfs_locks.py` + `chatfs_locks_test.py` committed alongside this
file. The stale-`__pycache__` incident from that session (a `.pyc`
compiled seconds before an `EX`→`SH` edit of equal byte length —
mtime+size freshness can never invalidate it) is worth remembering when
a test contradicts the source you're reading.

Follow-on session, same day: both stub tests filled (16/16, 0 stubs);
in passing, the file's three
inline `python -c` scripts (`CHILD_REENTER_W`, `CHILD_READ`, and the
new grandchild-spawner) were extracted to a `chatfs_locks_test/`
sibling directory as real `.py` files, referenced by path -- a repo-
wide grep confirmed no other embedded `python -c` scripts exist to
match. Full suite 78/78, basedpyright 0/0/0.
