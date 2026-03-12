---
why:
  - writable-control-files
  - procfs-control-plane
---

# Control Plane (Future)

Virtual files and directories that provide the procfs/sysfs-style control
interface.

**Status:** Future, unscheduled. Defined here for completeness.

## Virtual Nodes

- `control` — writable file; `write()` parses commands and triggers actions
- `status` — readable file; `read()` generates current state summary
- `.sync` — per-conversation; readable status + writable trigger
- `needs_sync/` — virtual directory; `readdir()` lists stale/missing entries

## Responsibilities

- Parse write commands (e.g., `sync <conv-id>`)
- Generate dynamic read content (not cached — computed on each `read()`)
- Integrate with an external job/action system (callback or channel)

## Design Constraint

Control plane reads are an exception to "no work on read" — they compute
dynamic content but must still be fast (no network, no subprocesses). They
read in-memory state, not external resources.
