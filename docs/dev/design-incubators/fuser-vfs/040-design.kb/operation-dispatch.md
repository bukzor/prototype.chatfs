---
why:
  - understand-fuse-operations
  - no-work-on-read
---

# FUSE Operation Dispatch

fuser exposes a trait (`Filesystem`) with methods for each FUSE operation.
The toy needs to implement:

**Read-path operations (all milestones):**
- `lookup` — resolve name within directory → inode + attributes
- `getattr` — return file/directory attributes for an inode
- `readdir` — list directory contents
- `open` — validate access, return file handle
- `read` — return file data at offset

**Write-path operations (future milestone):**
- `write` — accept data written to control files
- `setattr` — handle `touch` (timestamp update as sync trigger)

All read-path operations must be non-blocking. They look up the inode, find the
backing cache entry, and return data or ENOENT. No I/O beyond reading the cache.
