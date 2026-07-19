# Devlog: 2026-07-17 — chatfs_sh (close_fds=False) replaces chatfs_locks.run for production subprocess wiring

## Focus

Close the last item in `todo.kb/2026-07-17-000-chatfs-locks-...md`: route
every subprocess call site between chatfs verbs through a lock-fd-carrying
wrapper, so splat/render/browse invocations don't self-deadlock now that
`chatfs_locks` is reentrant only within a process tree that actually shares
the fd.

## Decisions

### chatfs_sh.run (close_fds=False) over chatfs_locks.run (pass_fds), for production call sites

**Rationale:** The plan going in was to grow `chatfs_locks.run`'s
`pass_fds=tuple(lock.fd for lock in registry.values())` wrapper and thread
it through all 13 call sites. Mid-task, redirected: use `chatfs_sh.py`
instead (a new shell-tracing `subprocess.run` wrapper, adapted from a
personal library, already present but unwired) and change its default
from Python's `close_fds=True` to `close_fds=False`.

`close_fds=False` alone isn't sufficient — Python's `os.open()` sets
`O_CLOEXEC` on every fd by default (PEP 446) independent of the
*subprocess*-side `close_fds` setting, so the lock fd still wouldn't
have crossed exec. `chatfs_locks._locked` now calls
`os.set_inheritable(fd, True)` right after opening the anchor fd, which
is what actually makes the fd survive any `close_fds=False` spawn.

The combination — inheritable-by-default fd + close_fds=False spawn —
means the fd-passing becomes an emergent property of two orthogonal,
generically-useful changes, not a locks-aware `run()` wrapper that every
future call site must specifically opt into. Any subprocess spawned via
`chatfs_sh.run` now carries the *whole* fd table, matching plain Unix
`exec()` semantics (a child inherits open fds unless the parent marked
them `O_CLOEXEC`) rather than Python's newer opt-out-by-default model.

Verified live (not just by the test suite, which doesn't exercise this
path): a lock held in a parent, with a child spawned via `chatfs_sh.run`
alone (no `pass_fds` involved), successfully borrowed the parent's write
lock — proving the fd crossed exec through inheritability, not through
any curated fd list.

**Alternatives considered:**
- Grow `chatfs_locks.run`'s signature to match every call site's needs
  (`stdin`/`stdout` for `run_pluck`, `stdout` for har-browse and render,
  bare argv for splat) and use it everywhere. Rejected: every new
  subprocess boundary would need to remember to route through the
  locks-aware wrapper specifically, and forgetting one is silent (a bare
  `subprocess.run` just self-deadlocks or blocks unexpectedly, with no
  import-time signal). The close_fds=False approach makes fd survival
  the default for *any* subprocess spawned through the shared
  `chatfs_sh.run`, whether or not the caller is thinking about locks
  that day.
- Delete `chatfs_locks.run` entirely once it became redundant for
  production use. Rejected: its test callers (`chatfs_locks_test.py`,
  `child_spawns_grandchild.py`) need `capture_output`/`timeout`/`env`,
  which `chatfs_sh.run`'s deliberately narrow signature (stdin/stdout
  only) doesn't carry, and growing it to match would be scope creep the
  task didn't ask for. Kept, docstring narrowed to "test/orchestration
  use" so a future reader isn't misled into using it for new production
  code.

## Conventions Established

- Lock fds (and, by extension, any fd meant to survive into a spawned
  chatfs verb) are opened inheritable at creation time, not made
  inheritable ad hoc per spawn site. `chatfs_sh.run`'s `close_fds=False`
  is what makes that inheritability actually reach the child; the two
  only work together.
- `chatfs_sh.run` is the production subprocess-spawning entry point for
  this codebase (tracing to stderr, Unix-style fd inheritance,
  always-raises). `chatfs_locks.run`'s explicit `pass_fds` remains valid
  but is now scoped to test/orchestration code that needs
  `capture_output`/`timeout`/`env`.

## Open Questions

- None new. The parent task's remaining items (capture()/meta.json
  through `staged`, view-symlink place-then-purge inversion, the five
  `[!TODO]` design docs, the kill-mid-flight test) are unaffected by
  this wiring change.

## References

- `todo.kb/2026-07-17-000-chatfs-locks--fill-test-stubs--migrate-chatfs-atomic-lock-helpers--wire-call-sites.md`
- `todo.kb/2026-07-13-000-Atomic-chat-dir-regeneration---stage-and-rename--never-rewrite-in-place.md`
- `chatfs_sh.py`, `chatfs_locks.py`
