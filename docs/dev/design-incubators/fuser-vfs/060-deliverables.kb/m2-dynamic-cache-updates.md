---
why:
  - vfs-core
  - cache-backed-virtual-fs
  - no-work-on-read
---

# M2 — Dynamic Cache Updates

The VFS reflects changes to the backing cache directory without remounting.
When external processes update the cache (simulating sync pipeline output),
the mounted filesystem shows new/changed/removed files.

## Acceptance

- Add a file to the cache directory; `ls` in mount shows it
- Modify a cached file; `cat` in mount shows new content
- Remove a cached file; `ls` in mount no longer shows it
- No explicit "refresh" action required — the VFS reads from cache on each
  operation (no internal caching layer)
