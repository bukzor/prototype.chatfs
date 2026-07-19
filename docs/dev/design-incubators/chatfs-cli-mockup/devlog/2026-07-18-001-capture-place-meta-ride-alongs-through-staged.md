# Devlog: 2026-07-18 — capture()/place_meta ride-alongs through staged()

## Focus

Close the "Ride-alongs" step of `todo.kb/2026-07-13-000-Atomic-chat-dir-
regeneration-...md`: `capture()`'s outputs (`cdp.jsonl`,
`conversation.json`) and `place_meta`'s `meta.json` still wrote in place
(unlink-then-write / truncate-overwrite), and the view-symlink cleanup
still purged before placing the fresh symlink — both destroy-then-
rebuild shapes the parent task exists to eliminate. `chatfs_atomic.py`
and the three providers' `path_render.py` already had the mechanism;
this session wired the remaining two call sites to it.

## Decisions

### One outer lock spanning multiple `staged()` calls, not one lock per call

Both `capture()` (cdp.jsonl + conversation) and `place_meta` (meta.json +
view symlink + purge) update more than one destination per logical
"transition." `chatfs_atomic.py`'s own module docstring had already
named both as the motivating examples for `chatfs_locks`' reentrancy
("a caller that must *span* multiple staged promotions as one
transition... wraps them in its own outer `chatfs_locks.write_locked
(anchor)`"), so the shape wasn't a new design choice — just applying it.

**Rationale:** without the outer lock, a cooperating reader using
`chatfs_locks.read_locked` could observe cdp.jsonl already updated to a
new capture but conversation.json still reflecting the old one (or
meta.json updated but the view symlink still stale) — individually
each destination is old-complete-or-new-complete (staged() guarantees
that alone), but the *pair* wouldn't be. The outer lock makes the whole
multi-file update one transition for cooperating readers; a
non-cooperating reader still never sees any single destination
partial, just possibly mismatched pairs momentarily (accepted, per the
mechanism's own documented contract).

**Alternatives considered:** locking per-call (each inner `staged()`
takes and releases its own lock) — rejected because it's exactly the
gap above; the whole point of `chatfs_locks`' reentrancy is that an
outer holder's lock is *borrowed*, not re-acquired, by nested calls.

### `_purge_view_symlinks` needs a `keep` exclusion for place-then-purge to work at all

The inversion (place the fresh view symlink, *then* purge stale ones
matching the same uuid) doesn't work as a naive reordering: the fresh
symlink's target also contains the uuid (`os.path.relpath(chat_dir,
...)`), so an unmodified purge sweep would immediately delete the
symlink it just placed — same bug, disguised. Added `keep: Path | None`
to `_purge_view_symlinks`, passed as the just-placed `title_link`, so
the sweep skips it by path equality.

**Rationale:** identity-scoped cleanup (sweep by "target contains
uuid") and "don't delete what you just placed" are in tension whenever
the placement itself matches the sweep's own criterion — which it
structurally always does here. `keep` is the minimal fix; it's an
exclusion by path (not by uuid), so it doesn't weaken the sweep's
identity-scoped-ness for every *other* stale symlink.

### Also staged the view-symlink placement itself, not just meta.json

The todo item's literal text ("meta.json through staged; view-symlink
place-then-purge inversion") only explicitly called out meta.json for
staging. Staged the symlink placement too (`with staged(title_link,
anchor=data_dir) as tmp: tmp.symlink_to(...)`) rather than the old
unlink-then-symlink_to two-step.

**Rationale:** the old two-step has its own (smaller) crash window —
a kill between unlink and symlink_to leaves the path absent — for the
*same-path* re-placement case (`place_meta` called twice with the same
label, e.g. a title-unchanged re-splat). `staged()` was already sitting
right there and handles files/symlinks with a single `os.replace`, so
using it cost nothing extra and closed that gap along with the bigger
one. Verified this doesn't change any existing test's expected calls
(the "different label" test still finds the stale symlink at a
different path and purges it as before).

## Conventions Established

- When a verb updates N destinations that must be treated as one
  transition, wrap all N inner `staged()` calls in one outer
  `chatfs_locks.write_locked(anchor)` — never call `staged()` N times
  unwrapped and rely on it happening fast. This is now the pattern in
  three places (`capture()`, `place_meta`, and the pre-existing
  `path_render.py` scripts' single-`staged()`-call case, which needs no
  wrapping since it's already just one destination).
- `_purge_view_symlinks(uuid, root, keep=...)` — any future call site
  that places a symlink before purging by the same identity it's
  placing under must pass `keep=` the placed path, or the purge
  immediately undoes the placement.

## Verification

Mutation-tested both new invariants by hand (revert fix → confirm new
test fails → restore), not a full `Skill(mutation-testing)` sweep —
scoped to the two specific gaps this session closed, matching the
project's established practice for small, well-understood diffs:

- Reverted `capture()` to unlink-then-write: both new `DescribeCapture`
  regression tests failed as expected (`'half-written' ==
  'prior capture'` and `'' == '{"prior": true}'`).
- Reverted `place_meta`'s ordering to purge-then-place: the new
  `it_places_the_fresh_symlink_before_purging_the_stale_one` failed
  (`fresh_link.is_symlink()` was `False` by the time purge ran).

5 new tests total. pytest 91/91, basedpyright 0/0/0. Commit `6132c4d`.

## Housekeeping

Deleted `todo.kb/2026-07-17-000-chatfs-locks--fill-test-stubs--
migrate-chatfs-atomic-lock-helpers--wire-call-sites.md` (flagged as a
`todo clear` candidate in the prior session's sessions.kb entry): all
Implementation Steps and Success Criteria were `[x]`, and its content
is cross-referenced by two existing devlogs
(`2026-07-17-000-chatfs-locks-stub-tests-and-child-script-extraction.md`,
`2026-07-17-001-chatfs-sh-close-fds-false-replaces-pass-fds-wiring.md`).
Rewrote `todo.md`'s dead markdown link to that file as plain prose
(same summary text, no link).

## Open Questions

None new. Parent task's remaining items: unwrap the five `[!TODO]`
design docs (`chat-as-directory.md`, `captured-vs-derived.md`,
`pipeline-implications.md`, `view-symlink.md`,
`deterministic-regeneration.md`), and the kill-mid-flight test per the
requirement's actual verification method.

## References

- `todo.kb/2026-07-13-000-Atomic-chat-dir-regeneration---stage-and-rename--never-rewrite-in-place.md`
- `chatfs_atomic.py` (module docstring — the "capture()'s two files,
  place_meta's promote-plus-symlink-sweep" example this session acted on)
- `design.kb/040-design.kb/deterministic-regeneration.md` (the
  place-then-purge `[!TODO]` block)
- `chatfs_layout.py`, `chatfs_layout_test.py`
