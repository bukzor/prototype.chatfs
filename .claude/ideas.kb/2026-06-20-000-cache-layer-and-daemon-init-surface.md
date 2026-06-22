# Cache layer + daemon init surface (design follow-ups)

Salvaged 2026-06-20 from `todo.kb/2026-04-20-000-review-lib-chatfs-for-integration.md`
during a subtask gc, before that file was deleted. Two design concerns it
raised were never tracked elsewhere; capturing them here so they resurface
when the daemon/cache design work begins.

## Cache layer design (in flux)

Plain-filesystem cache adjacent to the mount point: mtime = retrieval time,
HTTP-style cache-control metadata stored alongside content. FUSE-over-
obscured-content was ruled out (the mount replaces the kernel view); a cache
at a sibling path (e.g. `$XDG_CACHE_HOME/chatfs/`) is the clean answer.

Partial coverage already exists in `docs/dev/design.kb/040-design.kb/stack-split.md`
and `.claude/decision.kb/interactive-single-user-usage.md`; the sibling-path +
retrieval-mtime + cache-control specifics are not yet written down.

## Daemon setup / init surface

What `chatfs init` does, how providers are enrolled, mount-point
configuration. Not spec'd anywhere yet.

## Dropped from the same source (no action)

- `layer/` subtree cleanup — moot; `lib/chatfs` has since been removed.
- Maybe-P3 rewrite of the top-level CLI in Rust — speculative; overlaps the
  existing `packages/har-browse/dev.kb/rust-port.kb/` effort.
