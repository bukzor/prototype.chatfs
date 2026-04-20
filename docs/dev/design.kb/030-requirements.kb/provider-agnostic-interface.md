---
why:
  - multi-provider
---

# Provider-Agnostic Interface

The filesystem, cache, and rendering layers must not contain provider-specific
logic. Adding a new provider means implementing the capture and extraction
stages (BB1/BB2) for that provider — nothing else changes.

**Verification:** Add a second provider. The filesystem and cache code remain
untouched.
