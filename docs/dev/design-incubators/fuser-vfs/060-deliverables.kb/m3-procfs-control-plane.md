---
why:
  - control-plane
  - writable-control-files
---

# M3 — Procfs/Sysfs Control Plane (Future, Unscheduled)

Add writable virtual files and dynamic virtual directories implementing the
chatfs control plane pattern.

**Status:** Future, unscheduled. Tackle when ready, after M1 and M2 are solid.

## Acceptance

- `echo "sync foo" > control` triggers an observable callback
- `cat status` returns dynamically generated content
- `ls needs_sync/` lists entries derived from in-memory state (not cache dir)
- `touch conversations/abc123/branch-main.md` triggers a setattr callback
- All control operations are fast (no blocking, no network)
