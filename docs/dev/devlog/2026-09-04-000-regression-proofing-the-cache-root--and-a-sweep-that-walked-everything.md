# 2026-09-04 Regression-proofing the cache root, and a sweep that walked everything

## Focus

Two follow-ups from yesterday's `refresh` work: make the `--cache`
double-append impossible to re-introduce, and answer why the view-symlink
purge was walking the entire cache.

## What happened

### The double-append gets two guards, at different grains

The bug (fixed yesterday in ede34b3) was that `chatfs-provider-<p>-index
--cache X` wrote to `X/<p>/<p>/`. Nothing caught it because nothing was
wrong in any one place: `extract_cache` correctly appended the provider
segment, each child stage correctly appended it again from its own argv,
and the driver in between forwarded the wrong one of two identically-typed
paths. Every unit test passed with the bug present, and would have again.

The fix is to stop the two paths being the same type:

- `CacheRoot` -- what a command *takes* (`--cache <dir>`, all providers
  side by side).
- `ProviderRoot` -- what it *works in* (`$cache/$provider/`), produced
  only by `extract_cache`.
- `sh.stage(module, cache: CacheRoot, *args)` builds the argv for
  spawning a child stage. Passing the root you're working in is now a
  pyright error at the call site.

That covers the call sites that go through `stage`. It does not cover a
command written next year that spawns a child some other way, so the
second guard is behavioral: `provider/cache_layout_test.py` runs `index`
and `refresh` for all three providers as real subprocesses -- argv
parsed, children spawned -- and asserts the cache ends up with exactly
one provider directory, at the top. A stub `har-browse` first on PATH
replays a canned CDP stream, so there's no browser and no network; it
refuses any URL but the one the test named, loudly.

`$CHATFS_CACHE` is deleted from the test environment deliberately. It is
set in this author's shell, and a leaf that fell back to it would capture
into a real archive with a real browser -- which happened once, to an
agent, during this work.

Both guards were verified by re-introducing the bug in claude's index
driver: pyright reports `ProviderRoot ... not assignable to CacheRoot`,
and the integration test fails with `['claude', 'claude/claude']`.

**Unit tests where the mistake is expressible, integration tests where
it is only observable.** The type-level guard is cheap and instant but
only sees the code path it annotates; the process-level test is slower
but sees the tree, which is the thing that was actually wrong.

### The purge was walking everything, and owned too much

`_purge_view_symlinks` ran `root.rglob("*")` once per placed chat,
discarding `.chat/`, `.data/` and `trash/` *after* visiting them.
Measured against a replayed 1154-chat claude index: 5004 paths per sweep
(2310 of them storage, with `.chat/` still empty), 5.8M path visits per
index run, ~2.5 min. `refresh` pays it every run.

Three questions, three answers:

1. **Why purge at all?** A view path is derived from mutable inputs --
   title, creation time, label, and the derivation format itself. Rename
   a chat and the old symlink is still there; without the purge every
   rename leaves a duplicate and `find_view_path` returns an arbitrary
   one. This is real and stays.

2. **Why the whole cache?** No reason. `VIEW_TREE_GLOB` (`*=*`) roots the
   walk at the labeled date-view trees. The label is what makes it exact:
   `time_dir_for` writes every view tree as `f"{label}={year}"`, and no
   storage directory carries an `=`. Landed.

3. **Is the sweep the right shape at all?** No -- it re-derives per item
   what the placement already knew. A `view` back-pointer in
   `.data/$UUID/`, written inside the lock that already covers meta.json
   and the symlink, makes both the purge and `find_view_path` a readlink,
   and makes an unchanged view a no-op. Identity sweeping then becomes an
   explicit repair command, which is the occasion it was designed for: a
   derivation change is a migration event, not a per-item one. Not built
   -- tracked in the package taskfile, awaiting a go-ahead.

Narrowing the walk also fixed a correctness bug nobody had hit: the old
sweep deleted *any* symlink under the root whose target named the chat,
including a bookmark a user left there themselves. The purge owns what it
placed, and nothing else.

## Verified

`275 passed`; `basedpyright`: `0 errors, 7 warnings` (all pre-existing).
