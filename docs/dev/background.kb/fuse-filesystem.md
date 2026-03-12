---
source:
  - conversations.cleaned/05-fuse-implementation-details/159.assistant.text.md
---

# FUSE (Filesystem in Userspace)

FUSE allows implementing filesystem behavior in a normal process rather than
a kernel module. The kernel FUSE driver forwards filesystem operations (read,
readdir, getattr, etc.) to the userspace daemon, which responds with data or
error codes.

**Relevant properties for chatfs:**

- Enables exposing cached conversations as ordinary files
- The `fuser` Rust crate provides a `Filesystem` trait with methods for each
  FUSE operation
- Inodes are the fundamental addressing mechanism — each file/directory gets
  a stable numeric identifier
- The kernel may cache attributes and directory listings; TTL values control
  cache duration
- FUSE3 is the current protocol version (Linux 4.x+)

**Key challenge:** Understanding the FUSE operation model, inode lifecycle, and
performance characteristics under tool chatter (editors, ripgrep, completion).
This is the primary learning goal of the fuser-vfs incubator.
