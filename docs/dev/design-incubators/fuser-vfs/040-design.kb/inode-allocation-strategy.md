---
why:
  - stable-inodes
  - tool-chatter-resilience
---

# Inode Allocation Strategy

Inodes must be stable across mount cycles and cheap to compute. Two viable
approaches:

**Hash-based:** `inode = hash(path) & INODE_MASK`. Simple, deterministic, no
state. Risk: collisions (mitigated by large inode space on 64-bit).

**Table-based:** Maintain a path→inode map, persist across mounts. More complex
but collision-free. Better for dynamic content (new conversations appearing).

The toy should start with hash-based for simplicity. If collisions become a
problem in practice, switch to table-based. The chatfs design spec recommends
"pick a simple stable scheme early (even `inode = hash(path)`)."
