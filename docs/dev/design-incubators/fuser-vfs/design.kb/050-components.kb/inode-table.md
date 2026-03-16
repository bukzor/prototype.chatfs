---
why:
  - inode-allocation-strategy
  - stable-inodes
---

# Inode Table

Maps paths to inodes and inodes back to paths. Provides the stable, deterministic
inode assignments the VFS depends on.

## Responsibilities

- Allocate inodes for paths (hash-based initially)
- Reverse lookup: inode → path
- Report file type (directory vs. regular file) and attributes
- Scan cache directory to discover available entries

## Interface

```rust
struct InodeTable { ... }

impl InodeTable {
    fn lookup(&self, parent: u64, name: &OsStr) -> Option<(u64, FileAttr)>;
    fn getattr(&self, ino: u64) -> Option<FileAttr>;
    fn readdir(&self, ino: u64) -> Vec<(u64, FileType, OsString)>;
}
```
