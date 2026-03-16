---
why:
  - reusable-vfs-crate
---

# Tool Chatter Resilience

Editors, ripgrep, shell completion, and file watchers generate many rapid
filesystem operations (stat, readdir, getattr). The VFS must handle these
without performance degradation, errors, or side effects.

**Verification:** Open the mount directory in an editor (vim, VSCode). Run
`rg "pattern"` across the mount. No hangs, no errors, no unexpected behavior.
