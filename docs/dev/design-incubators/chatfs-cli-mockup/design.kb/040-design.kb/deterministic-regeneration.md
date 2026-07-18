---
why:
  - atomic-cache-updates
  - pipeline-composability
---

# Deterministic Regeneration

Every pipeline stage presumes its outputs are stale and rebuilds them
from scratch. There are no freshness caches in the user-facing scripts.

## Rule

Before a verb's outputs become visible, any prior artifact they
supersede is removed. After the verb runs, the outputs are a pure
function of the inputs and the verb's code — never a mixture of old
and new.

A verb builds its complete output in a destination-adjacent scratch
(`.tmp` sibling) and atomically promotes it over the prior artifact
(mechanism: `chatfs_atomic.py`) -- supersession happens at the rename,
with no advance purge and no window where outputs are absent, partial,
or mixed. Failed attempts are preserved as `.fail` siblings
(latest-wins, cleared by the next success), so a crash leaves the
in-progress bytes on disk for inspection. Identity-scoped symlink
cleanup is place-then-purge: the new view symlink is placed first, then
stale ones for the same identity are swept, excluding the fresh one.

This applies to:

- `index browse` — re-runs har-browse every time; no mtime check on
  the tee'd CDP debug file.
- `conversation url browse` and `conversation path browse` —
  `capture()` stages `cdp.jsonl` and `conversation.json` into
  `.data/$UUID/` under one outer write lock; a failed browse leaves the
  prior `cdp.jsonl` untouched, a failed pluck leaves the prior
  `conversation.json` untouched.
- `index splat` — calls `place_meta` per item; `meta.json` staged into
  `.data/$UUID/`; the view symlink is placed, then stale symlinks for
  the same identity are purged (place-then-purge).
- `conversation path render` — builds the entire derived surface
  (`chat.md`, `messages/`, the `.data` inspection symlink) in one
  staged scratch and atomically promotes it as a single swap of
  `.chat/$UUID/` (see `chat-as-directory.kb/pipeline-implications.md`).

## Identity-scoped cleanup

The cleanup above is mostly path-scoped — "rm whatever lives at the
same address we're about to write." That suffices when a verb's output
always lives at the same place.

When derivation logic puts the same identity at different paths over
time — e.g. a chat's view symlink was at the UTC ts-dir last run, lives
at a local-zone ts-dir this run — cleanup must be by identity, not by
path.

The general form: **before a verb writes its outputs, it removes any
prior artifact those outputs supersede, regardless of where the prior
artifact lived.**

For view symlinks targeting `.chat/$UUID/…`, the cleanup is a sweep,
run *after* the fresh symlink is placed (`keep` excludes it so the
sweep doesn't immediately undo the placement it's meant to follow):

```python
def _purge_view_symlinks(uuid: str, root: Path, *, keep: Path | None = None) -> None:
    for path in root.rglob("*"):
        rel_parts = path.relative_to(root).parts
        if ".chat" in rel_parts or ".data" in rel_parts:
            continue  # storage-internal symlinks, not views
        if path == keep:
            continue
        if path.is_symlink() and uuid in os.readlink(path):
            path.unlink()
```

This keeps the storage layer (`.chat/$UUID/`) authoritative — the only
place a UUID's view symlinks ever resolve to — while letting derived
views (`YYYY/MM/…`) heal automatically when their derivation logic
changes.

A future improvement could move the sweep to a background thread; for
now an inline scan is fine.

Other contexts where this applies: any pluggable view tree (by-tag,
by-model), and anywhere else identity is bound to a path that
derivation logic may relocate.

## Why not freshness caches

Stage-skipping caches hide code changes (in the stage and in external
tools it shells out to), upstream input changes, and partial-write
failures. The full rationale and history of the removal lives in
`adr/2026-04-29-000-no-freshness-caches.md`.
