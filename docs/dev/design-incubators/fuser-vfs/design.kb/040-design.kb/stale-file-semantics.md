---
why:
  - no-work-on-read
  - serve-static-directory-tree
---

# Stale File Semantics

Files can appear in directory listings but fail when opened. This is legal and
used by many virtual filesystems.

**Implementation:**
- `getattr()` succeeds normally (file exists, has size/permissions)
- `readdir()` includes the file
- `open()` fails with `EAGAIN` or `ESTALE` if stale

**Error choice:**
- `EAGAIN` (Resource temporarily unavailable) — recommended, communicates "file
  exists but cannot be served now"
- `ESTALE` (Stale handle) — also appropriate, common in network FS when cache
  expires
- `EEXIST` is wrong (means "file already exists," for `create()`/`mkdir()`)
- `ENOENT` is misleading if the file was just listed

**Prior art:** `/proc` entries sometimes return `EAGAIN`; network FS use
`ESTALE`; some FUSE mounts return `ESTALE` when cache expires.

**UX enhancement:** Pair stale files with hint files (`.sync`,
`.instructions`) that print the exact command to run for refresh.
