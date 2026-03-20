---
why:
  - architectural-invariants
source:
  - docs/design-incubators/dynamic-routing/demo.py
---

# POSIX Error Semantics

All VFS framework errors are filesystem errnos, never language exceptions.
User-facing behavior matches what POSIX applications expect from any filesystem.

- **ENOENT** — entry not found during path resolution (missing segment in
  `list()` results, or name not in static children).
- **ESTALE** — inode exists in the translation table but path resolution fails.
  The entity was known but has since vanished. Same semantics as NFS stale file
  handles.
- **ENOTDIR** — path resolution attempted to traverse through a file.
- **EISDIR** — read attempted on a directory.

Internal errors (e.g. Python `KeyError` from a missing dict lookup during
resolution) are caught and translated to the appropriate errno. No framework
exceptions propagate to the FUSE layer.
