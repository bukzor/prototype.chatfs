---
why:
  - architectural-invariants
---

# Atomic Cache Updates

Cache updates follow a staging → rename swap pattern:

1. Write new content to `staging/<jobid>/`
2. `fsync` the staging directory
3. Rename `staging/<jobid>/` to `current/` (atomic on POSIX)
4. Previous `current/` becomes `previous/` (last-known-good)

Readers always serve from `current/`. A failed update never corrupts the cache —
it leaves `current/` untouched and preserves artifacts/logs for debugging.
