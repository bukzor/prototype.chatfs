---
why:
  - atomic-cache-updates
  - pipeline-composability
---

# Deterministic Regeneration

Every pipeline stage presumes its outputs are stale and rebuilds them
from scratch. There are no freshness caches in the user-facing scripts.

## Rule

Before a verb writes its outputs, it removes any prior artifact those
outputs supersede. After the verb runs, the outputs are a pure function
of the inputs and the verb's code — never a mixture of old and new.

This applies to:

- `index browse` — re-runs har-browse every time; no mtime check on
  the tee'd CDP debug file.
- `conversation url browse` — derives `$UUID` from the URL; writes
  captured artifacts directly into `.chat/$UUID/`; runs identity-scoped
  view-symlink cleanup before placing the date-view symlinks.
- `conversation path browse` — addresses by `.chat/$UUID/`; removes
  prior `cdp.jsonl` and `conversation.json` before re-capturing.
- `index splat` — calls `place_meta` per item; `meta.json` overwritten
  in `.chat/$UUID/.data/`; view dir-symlinks identity-purged then
  placed.
- `conversation path render` — operates on `.chat/$UUID/`; purges
  non-captured contents (allowlist `{".data"}`; see
  `chat-as-directory.kb/captured-vs-derived.md`), runs `chatgpt-splat`,
  writes `chat.md`.

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

For view symlinks targeting `.chat/$UUID/…`, the cleanup is a sweep:

```python
def _purge_view_symlinks(uuid: str, root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_symlink() and uuid in os.readlink(path):
            path.unlink()
```

This keeps the storage layer (`.chat/$UUID/`) authoritative — the only
place a UUID's data ever lives — while letting derived views
(`YYYY/MM/…`) heal automatically when their derivation logic changes.

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
