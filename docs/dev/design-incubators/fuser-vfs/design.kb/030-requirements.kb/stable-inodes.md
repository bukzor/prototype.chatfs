---
why:
  - understand-fuse-operations
---

# Stable Inodes

Inode numbers are deterministic for a given path. Unmounting and remounting
produces the same inode assignments. Tools that cache inodes (editors, file
watchers) do not see phantom changes.

**Verification:** Run `stat --format=%i` on the same path across mount cycles;
values match.
