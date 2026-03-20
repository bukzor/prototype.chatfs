---
why:
  - architectural-invariants
source:
  - packages/chatfs-fuser/sketch.py
---

# Inode Lifecycle

Inodes are assigned lazily during `lookup` and `readdir` and are stable for
their lifetime — once a path has an inode, that mapping does not change. Stale
inodes (path no longer resolves) return ESTALE on access.

## Current implementation

Append-only table, no revocation. Simplest correct scheme at chatfs's scale
(hundreds of conversations, not millions).

## Future extension

FUSE's `forget(ino)` callback signals when the kernel drops all references to
an inode, enabling reaping without GC sweeps or heuristics. The policy (stable
assignment, ESTALE on stale access) is unchanged by whether reaping is
implemented.
