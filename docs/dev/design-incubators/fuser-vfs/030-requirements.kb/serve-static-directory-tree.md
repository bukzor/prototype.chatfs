---
why:
  - reusable-vfs-crate
  - understand-fuse-operations
---

# Serve a Static Directory Tree

Mount a virtual filesystem that presents a fixed directory tree with file
contents drawn from a backing store (in-memory or on-disk cache directory).

**Verification:**
- `ls` shows expected directories and files
- `cat` returns correct file contents
- `stat` reports reasonable sizes, timestamps, and permissions
- `find` traverses the full tree without errors
