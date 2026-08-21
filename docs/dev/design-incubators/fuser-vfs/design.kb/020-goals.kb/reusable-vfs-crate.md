---
why:
  - ../010-mission.kb/fuse-filesystem-learning.md
---

# Reusable VFS Crate

The toy should produce a crate that directly becomes the foundation for chatfs's
filesystem layer. Not a throwaway prototype — the inode management, path
resolution, and FUSE operation handling should be production-quality and
provider-agnostic.
