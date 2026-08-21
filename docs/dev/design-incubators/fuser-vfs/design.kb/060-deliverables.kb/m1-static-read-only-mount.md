---
why:
  - ../050-components.kb/vfs-core.md
  - ../050-components.kb/inode-table.md
  - ../030-requirements.kb/serve-static-directory-tree.md
---

# M1 — Static Read-Only Mount

Mount a virtual filesystem backed by a cache directory. All standard read
operations work.

## Acceptance

- `mount` succeeds; `ls` shows directory tree matching cache contents
- `cat <file>` returns correct content
- `stat` reports stable inodes, reasonable sizes and timestamps
- `find` traverses without errors
- `rg "pattern"` searches files without hangs
- Opening mount directory in an editor does not cause errors
- `umount` succeeds cleanly
