---
why:
  - reusable-vfs-crate
---

# No Expensive Work on read()

All FUSE read operations serve from cache or in-memory state. No network
requests, no subprocess invocations, no file generation. Read handlers return
data or an error code — nothing else.

This is architectural invariant #2 from the chatfs design.

**Verification:** Mount the VFS with the network disabled. All reads succeed
(or return EAGAIN for stale entries). No timeouts.
