# Devlog: 2026-07-18 — design-doc unwrap and kill-mid-flight tests close the atomic-regen task

## Focus

Closed the last two open items in `todo.kb/2026-07-13-000-Atomic-chat-dir-
regeneration-...md`: unwrap the five `[!TODO]` design-doc blocks, and add
the kill-mid-flight test the requirement's own verification method names
("kill a sync mid-flight; the mount continues serving the previous content
without errors"). All Implementation Steps and Success Criteria in the
task file are now `[x]` — this closes the task that's been the incubator's
top tactical priority since 2026-07-13.

## Decisions

### Verify against ground truth before unwrapping, not just delete the markup

Before touching any of the five docs (`chat-as-directory.md`,
`captured-vs-derived.md`, `pipeline-implications.md`, `view-symlink.md`,
`deterministic-regeneration.md`), read the actual landed code each block
described as future state: `chatfs_atomic.py` in full, and
`chatfs_layout.py`'s `place_meta`/`capture`/`_purge_view_symlinks`, and one
provider's `path_render.py` leaf. Every claim held — confirms the
2026-07-17/18 wiring sessions landed exactly what the design settled on
2026-07-15, no drift.

Beyond pure markup removal (the `Skill(llm-design-kb)` convention: a
`[!TODO]` block's prose is already the descriptive sentence once the
behavior lands, so landing it should be near-zero-edit): `chat-as-
directory.md`'s layout diagram needed redrawing (`.data/$UUID` moved
from nested-inside to sibling-of `.chat/$UUID`), and its "Storage vs
view"/"Identity is primary" sections still described one storage tree,
not two. `captured-vs-derived.md`'s "Allowlist `.data/`, purge the rest"
section described a mechanism (the purge-allowlist) that no longer
exists — the `[!TODO]` block that preceded it said as much ("goes away
with it") but nothing had actually rewritten the section underneath it.
`pipeline-implications.md` was rewritten per-script wholesale against
the real code rather than patched, since nearly every sentence had
changed. `deterministic-regeneration.md`'s `_purge_view_symlinks` code
sample was still the pre-`keep`-param version — a second, independent
kind of staleness the `[!TODO]` block itself didn't flag, caught only by
diffing the sample against the real function.

Also fixed, found along the way: `chatfs_atomic.py`'s own module
docstring still said "Design sketch -- imported nowhere yet," false
since `chatfs_layout.py` has imported it since 2026-07-17's wiring.

### Kill-mid-flight: instrument the child script, not the module under test

The existing `chatfs_atomic_test.py` already had a `DescribeCrashRecovery`/
`DescribeRecover` crash matrix, but every case worked by hand-crafting the
on-disk fingerprint a kill would leave (write a stale `.tmp` file
directly, etc.) or by raising a Python exception mid-populate — neither is
an actual kill. `chatfs_locks_test.py` had the real-subprocess pattern
this repo already uses (`chatfs_locks_test/child_*.py`, spawned via
`subprocess`), but its synchronization relies on the flock itself
blocking the child — no equivalent primitive exists for "pause exactly
between these two `os.rename` calls."

Built a new primitive for that: the child script monkeypatches the
specific syscall (`os.rename` or `os.unlink`) *from itself*, not from
`chatfs_atomic.py`, so the module under test stays untouched. On the
call of interest, the spy prints `"ready"` (flushed) and immediately
self-`SIGSTOP`s (`os.kill(os.getpid(), signal.SIGSTOP)`). The parent's
`subprocess.Popen(...).stdout.readline()` blocks until that line arrives
— no sleep, no timing race, the print is the synchronization — then
sends `SIGKILL`. A stopped process still dies immediately on `SIGKILL`
per POSIX (unblockable, uncatchable, and stop state doesn't defer it),
so the child is guaranteed to die at exactly the instrumented point, one
call past the boundary being tested.

Four boundaries, matching `recover()`'s own docstring plus one more:

- mid-populate (the scratch has partial bytes, nothing promoted yet)
- between `_swap_via_old`'s two renames (dst momentarily absent, `.old`
  holds the complete old version) — forces the RENAME_EXCHANGE-
  unsupported fallback to reach this path at all
- after both renames, before the final `.old` cleanup (dst already new,
  `.old` superseded but not yet swept) — same forced fallback
- mid-`shutil.rmtree` cleanup following a *real* RENAME_EXCHANGE
  promote (this filesystem supports it — checked empirically first) —
  proves dst is already fully-new the instant the atomic exchange
  commits, regardless of what happens to the displaced old copy
  afterward

**Alternative considered:** sleep-based timing to approximate "kill
during X." Rejected outright, not just as a preference — a sleep gives
no guarantee the kill lands in the intended window rather than before or
after it, which would make the test either flaky or silently
non-representative of the boundary it claims to cover.

## A real bug, caught in the test helper itself

First run hung indefinitely. Cause: the helper read `proc.stderr.read()`
*unconditionally*, right after the readiness `readline()`, intending it
only for a failure message — but `.read()` with no size argument blocks
until EOF, and EOF on a pipe only happens when the writing end (the
child) exits. A child that reached `"ready"` is merely `SIGSTOP`ped, not
exited, so its stderr pipe stays open indefinitely until *something*
kills it — which was supposed to be the next line, never reached. Fixed
by moving the stderr drain to only the already-exited failure branch
(`proc.communicate()`, called only when the child never printed
`"ready"` at all, at which point it has necessarily already exited).

## Verification

Each boundary's precision was hand mutation-tested — not
`Skill(mutation-testing)`'s full sweep, scoped to what's genuinely novel
here (the real-kill synchronization, not `chatfs_atomic.py`'s pre-tested
logic):

- Swapped which `os.rename` call triggers the pause in the
  between-renames test (1st → 2nd call): correctly failed
  (`assert not dst.exists()` — dst existed, since the 2nd rename had
  already run).
- Same swap in reverse for the before-old-cleanup test (2nd → 1st):
  correctly failed with `FileNotFoundError` reading `new_file` (only
  the 1st rename had run).
- Forced `_exchange` unsupported in the exchange-cleanup test: correctly
  failed (`sibling(dst, "tmp").is_dir()` was `False` — under the forced
  fallback, the spied `os.unlink` call still fires, but from a
  different, unintended code path inside `_swap_via_old`'s own `.old`
  cleanup, producing the wrong on-disk layout for what the test asserts).

All three mutations reverted after confirming failure. Also verified no
flakiness: 5x repeat run of the 4 new tests, all green, ~0.3s total.

pytest 95/95 (91 → 95, four new), basedpyright 0/0/0. No stray processes
left behind (checked via `ps` after the earlier hang, and after the
final clean run).

## Housekeeping

`todo.kb/2026-07-13-000-...md` is now fully closed (every Implementation
Step and Success Criterion `[x]`) but **not** deleted via the usual
`todo clear` convention — its own "Notes" section says it re-homes with
the code at graduation, and unlike the sibling child task deleted
2026-07-18 earlier today, this file's "Alternatives rejected" section
(specifically the `redo`-tool rejection) isn't duplicated in any devlog
or ADR; deleting it would lose that rationale. `todo.md`'s own entry for
this task marked `[x]` with a closing summary, left in place rather than
stripped (per `todo clear`'s own convention of leaving verified-done
entries until an explicit clear pass, since `[x]` doesn't yet outnumber
`[ ]` in this file).

## Open Questions

None. The parent task (and this incubator's top tactical priority since
2026-07-13) is closed. Next up per `todo.md`: the AI Studio provider
parity ladder, or the strategic claude-code-as-next-provider item.

## References

- `todo.kb/2026-07-13-000-Atomic-chat-dir-regeneration---stage-and-rename--never-rewrite-in-place.md`
- `chatfs_atomic.py`, `chatfs_atomic_test.py` (`DescribeKillMidFlight`)
- `chatfs_atomic_test/child_kill_during_populate.py`,
  `child_kill_between_renames.py`, `child_kill_before_old_cleanup.py`,
  `child_kill_during_exchange_cleanup.py`
- `design.kb/040-design.kb/chat-as-directory.md`,
  `deterministic-regeneration.md`,
  `chat-as-directory.kb/{captured-vs-derived,pipeline-implications,view-symlink}.md`
- `docs/dev/design.kb/030-requirements.kb/atomic-cache-updates.md` (the
  verification method this session's new tests satisfy)
