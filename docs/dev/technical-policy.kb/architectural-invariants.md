---
why:
  - design-spec
---

# Architectural Invariants

Seven constraints that define the architecture. Breaking any breaks the design.

1. **Black-box boundary:** BB1 capture + BB2 extract + BB3 emit are opaque,
   assumed to exist
2. **No work on `read()`:** Cached-only reads; explicit triggers (`touch` /
   `control` write)
3. **Stale semantics:** `ls` shows entries; `open`/`read` returns
   `EAGAIN`/`ESTALE`; `.sync`/`needs_sync/` explains
4. **Procfs/sysfs control plane:** `control`, `status`, `needs_sync/` layout
5. **Atomic cache:** Staging dir → rename swap; preserve last-known-good
6. **Provider plugin model:** `/chatgpt/`, `/claude.ai/` etc. with identical
   outer behavior
7. **Linux-first (FUSE3) + WSL2 counts as Linux**

**Gotchas:**
- Tool chatter (editors, ripgrep, completion) causes many FS ops — the
  "no network on read" + explicit trigger design neutralizes this
- Pick a simple stable inode scheme early (`inode = hash(path)`) to avoid
  weirdness with tools that cache inodes

See [data/todo-llmfs.chatgpt.com.splat/extracted/03-architectural-invariants.md]
for origin and endorsement context.
