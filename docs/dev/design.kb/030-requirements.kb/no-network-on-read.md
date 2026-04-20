---
why:
  - safe-automation
  - lazy-filesystem
---

# No Network Activity on Read

All filesystem read operations (readdir, getattr, open, read) serve from
cache. No network requests, no subprocess invocations, no file generation
during reads.

This is load-bearing. Editors, ripgrep, shell completion, and file watchers
generate rapid, speculative reads. If reads triggered network activity, the
system would be unusable — and from the provider's perspective,
indistinguishable from automated scraping.

**Verification:** `tcpdump` shows zero network traffic during `find`, `grep -r`,
or editor indexing of the mount.
