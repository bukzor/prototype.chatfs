# Learn FUSE Filesystem Mechanics

chatfs's end state is a user-space filesystem exposing cached LLM conversations
as files. The FUSE layer is the user-facing surface — it determines whether the
system feels like "just files" or like a clunky tool. But we have zero experience
with FUSE programming: inode management, path resolution, readdir/getattr/read
handlers, or the procfs-style control plane the architecture requires.

## The Problem

The chatfs architecture (from the design spec) demands:

- Cached-only reads — FUSE handlers must be fast, no network on `read()`
- Stale signaling — `ls` shows entries, `open`/`read` returns EAGAIN/ESTALE
- Procfs/sysfs control plane — `.sync`, `needs_sync/`, `control`, `status` files
  that accept writes and produce dynamic reads
- Atomic cache serving — FUSE always serves from `current/`, swapped via rename
- Provider-agnostic mount — `/mnt/llmfs/chatgpt/`, `/mnt/llmfs/claude.ai/` with
  identical outer behavior

These are FUSE-specific concerns that can't be learned from the JSONL pipeline
work. A toy filesystem isolates the "how does fuser actually work?" question
from provider logic, caching, and orchestration.

## Who Benefits

The chatfs developer (user). This subproject de-risks the FUSE mount layer by
building confidence with inode/path mapping, filesystem operations, and the
control plane pattern before integrating with the rest of chatfs.

## What Success Looks Like

After completing this subproject, the developer can confidently build the chatfs
mount layer because they understand:

- fuser's trait API and how FUSE operations map to Rust methods
- Inode allocation and path↔inode mapping strategies
- How readdir, getattr, open, and read interact
- How to implement writable control files (procfs pattern)
- Performance characteristics and gotchas (tool chatter, inode stability)

The toy VFS crate is directly reusable as the foundation for chatfs's
filesystem layer.
