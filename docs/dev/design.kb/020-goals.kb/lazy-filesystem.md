---
why:
  - chatfs
background:
  - fuse-filesystem
  - google-piper-precedent
---

# Lazy Filesystem Presentation

Conversations should appear as a mounted filesystem — browsable with ls,
searchable with grep, readable with cat. The filesystem serves from cache;
it never blocks on network access during reads.

The mount is thin. Expensive work (capture, extraction, rendering) happens
outside the read path, triggered explicitly by the user. This follows the
Google Piper precedent: thin FUSE layer + background workers.
