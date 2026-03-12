---
why:
  - procfs-control-plane
---

# Writable Control Files (Future)

Virtual files that accept writes and trigger actions. Virtual files that produce
dynamic content on read. This enables the chatfs control plane:

- `control` — write `sync <conv>` to trigger refresh
- `status` — read to see daemon/job state
- `.sync` — per-conversation instructions/status
- `needs_sync/` — directory listing stale/missing conversations

**Status:** Future, unscheduled. Depends on mastering basic FUSE operations first.

**Verification (when implemented):**
- `echo "sync foo" > control` triggers an observable action
- `cat status` returns dynamic content reflecting current state
- `ls needs_sync/` lists entries that change based on cache state
