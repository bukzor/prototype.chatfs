---
why:
  - cache-backed-virtual-fs
  - operation-dispatch
---

# VFS Core

The main struct implementing fuser's `Filesystem` trait. Dispatches FUSE
operations to the inode table and cache reader.

## Responsibilities

- Implement `lookup`, `getattr`, `readdir`, `open`, `read`
- Translate inodes to paths via the inode table
- Read file contents from the cache directory
- Return appropriate error codes (ENOENT, EAGAIN)

## Interface

```rust
struct ChatfsVfs {
    inodes: InodeTable,
    cache_root: PathBuf,
}

impl Filesystem for ChatfsVfs { ... }
```

## Notes

Provider-agnostic. Knows nothing about conversations, messages, or providers.
It serves a directory tree backed by a cache directory. What populates that
cache is someone else's problem.
