---
why:
  - architectural-invariants
source:
  - docs/design-incubators/dynamic-routing/demo.py
---

# Stateless Re-evaluation

Every FUSE access re-walks from root, re-calling user callbacks at each path
segment. No framework-level caching. `entry_valid=0` extends this to the kernel
(every lookup/getattr/readdir hits the FUSE daemon).

Caching is the caller's responsibility. The VFS framework lacks the information
to determine cache validity — only the user's callbacks know when their data is
stale. Callers that find re-evaluation expensive should cache in their callbacks.

## Consequences

- **Fresh data or fresh errors** on every access — no stale reads from the
  framework itself.
- **Races are standard POSIX behavior**, not a framework deficiency. `readdir`
  may return entries that are gone by the time the caller accesses them — same
  as `/proc` or any ext4 directory with concurrent deletes.
- **Self-healing.** Data that disappears and reappears resolves correctly with
  no special handling — the same inode maps to the same path, and the callback
  re-evaluates to fresh content.
