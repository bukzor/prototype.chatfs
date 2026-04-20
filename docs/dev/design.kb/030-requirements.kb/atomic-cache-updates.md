---
why:
  - lazy-filesystem
---

# Atomic Cache Updates

Cache updates must never leave the filesystem in an inconsistent state. A
failed sync must not corrupt existing cached data. Readers always see either
the old complete state or the new complete state, never a partial update.

**Verification:** Kill a sync mid-flight. The mount continues serving the
previous content without errors.
