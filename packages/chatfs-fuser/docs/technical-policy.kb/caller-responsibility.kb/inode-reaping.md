---
why:
  - inode-lifecycle
source:
  - docs/design-incubators/dynamic-routing/demo.py
---

# Inode Reaping

Not implemented. Inode table is append-only.

Future: FUSE's `forget(ino)` signals when the kernel drops all references,
enabling reaping without GC sweeps. The inode lifecycle policy (stable
assignment, ESTALE on stale access) is unchanged by whether reaping is
implemented.
