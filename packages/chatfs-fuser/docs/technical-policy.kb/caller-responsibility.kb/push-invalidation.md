---
why:
  - stateless-re-evaluation
source:
  - docs/design-incubators/dynamic-routing/demo.py
---

# Push Invalidation

Not implemented. Future work.

With `entry_valid=0`, the kernel re-validates on every access, so freshness is
entirely re-evaluation-driven. Push invalidation (`notify_inval_entry`) would
allow nonzero timeouts for better performance without staleness — but the
framework works correctly without it.
