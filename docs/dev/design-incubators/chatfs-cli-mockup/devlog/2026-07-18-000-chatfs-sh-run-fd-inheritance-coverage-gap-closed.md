# Devlog: 2026-07-18 — chatfs_sh.run fd-inheritance coverage gap closed

## Focus

Close the coverage gap flagged in `todo.md`/devlog `2026-07-17-001-...md`:
no automated test exercised `chatfs_sh.run`'s fd-inheritance path
specifically (only hand-verified) — the existing
`DescribeSubprocessReentry` tests all spawn through `chatfs_locks.run`'s
`pass_fds`, not the `close_fds=False` path production actually uses.

## Decisions

### Grow `chatfs_sh.run` by one parameter (`timeout`), not `env`

Writing `it_reenters_the_parents_write_lock_via_chatfs_sh_run` needed two
things the existing `child()` test helper gets from `chatfs_locks.run`:
an injected `PYTHONPATH` (so the spawned script can import `chatfs_locks`)
and a bounded wait (so a real regression fails fast instead of hanging
the suite — the child would block on `flock(LOCK_EX)` forever if fd
inheritance broke, since the parent's `with write_locked(...)` doesn't
release until the child returns).

- `PYTHONPATH`: no new parameter needed. `chatfs_sh.run` already calls
  `subprocess.run(..., env=None)`, which inherits the live process
  environment. `monkeypatch.setenv("PYTHONPATH", str(HERE))` in the test
  achieves the same effect the old helper's explicit `env={**os.environ,
  ...}` dict did, without touching production code.
- `timeout`: no equivalent existed. Added `timeout: float | None = None`
  to `chatfs_sh.run`, passed straight through to `subprocess.run`.
  Default `None` preserves current behavior for all 13 production call
  sites (grepped: none pass or need it). Matches the module's own
  docstring invitation ("grow it as needed") — this is a genuine need
  (test hang-safety), not test convenience for its own sake.

Deliberately did not add `env` or `capture_output` — nothing needs them,
and the prior session's devlog already rejected growing this module's
signature to match `chatfs_locks.run`'s test-only surface.

### Verified the test actually detects the regression it targets

Red-green alone (TypeError on the unimplemented `timeout` kwarg, then
green once added) only proves the test *runs* — it doesn't prove it
*catches* a broken fd-inheritance path, since the same code path is
already covered end-to-end by
`it_reenters_the_parents_write_lock_without_deadlock` via
`chatfs_locks.run`. Mutation-tested by hand: flipped `chatfs_sh.run`'s
`close_fds=False` to `True`, reran just the new test — it failed with
`subprocess.TimeoutExpired` after 10s (not a hang) and stderr showed
`chatfs_locks`'s "not open" warning, i.e. the child's fresh `flock`
blocked on the parent's still-held write lock exactly as expected absent
inheritance. Reverted the mutation immediately after observing the
failure.

## Conventions Established

- `chatfs_sh.run`'s `timeout` parameter is documented in its own
  docstring as unused by production, existing solely so tests can bound
  a would-be deadlock — future readers shouldn't infer a production need
  from its presence.

## Open Questions

None new. Parent task's remaining items (capture()/meta.json through
`staged`, view-symlink place-then-purge inversion, the five `[!TODO]`
design docs, the kill-mid-flight test) are unaffected.

## References

- `todo.kb/2026-07-13-000-Atomic-chat-dir-regeneration---stage-and-rename--never-rewrite-in-place.md`
- `devlog/2026-07-17-001-chatfs-sh-close-fds-false-replaces-pass-fds-wiring.md`
- `chatfs_sh.py`, `chatfs_locks_test.py`
