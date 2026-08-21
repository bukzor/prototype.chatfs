---
why:
  - ../020-goals.kb/reusable-vfs-crate.md
---

# Crate Selection

**Linux (primary target):**
- `fuse3` — async-first, Tokio-native, built for async/await. Best if already
  in Tokio ecosystem. Maps naturally to "enqueue work; return quickly."
- `fuser` — widely used Rust FUSE rewrite (not just bindings). Stable, broad
  ecosystem. Has `fuser-async` variant.
- `polyfuse` — async-leaning but under development; use with caution.

**macOS:**
- Uses macFUSE (formerly OSXFUSE) as kernel bridge.
- `fuser` has most direct macOS support claim in docs (with caveats).
- `fuse3` has macOS marked as unstable.
- Lowest-effort path: `fuser` + macFUSE.

**Windows (future):**
- No FUSE; use WinFsp or Dokan.
- `winfsp` crate: wraps WinFSP service architecture, implement a trait.
- `dokan` crate: handler trait + mount model.
- Recommendation: start with `winfsp`.

**Cross-platform strategy:**
1. Platform-agnostic core (path→inode mapping, cache/index, job queue, renderers)
2. Per-OS mount backends (Linux+macOS: `fuser`; Windows: `winfsp`)

Write logic once; implement 2–3 thin adapters for mounting/session management.

**Practical pick for the toy:** Start with `fuser` for broadest compatibility,
or `fuse3` if pure Linux + async is the priority.
