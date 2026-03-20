---
why:
  - stateless-re-evaluation
source:
  - design-session (2026-03-20)
  - docs/design-incubators/dynamic-routing/demo.py
---

# Caching

The framework re-evaluates callbacks on every access. No framework-level cache.

Only the caller knows when data is stale. Callers who find re-evaluation
expensive should cache in their callbacks.
