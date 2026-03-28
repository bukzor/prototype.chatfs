---
why:
  - safe-automation
background:
  - policy-safe-automation-boundary
---

# Opaque Extractor Boundary

The extraction pipeline (BB1 capture + BB2 pluck) is a black box. Its existence
and outputs are accepted as given facts. Assistants must not help design,
implement, or debug the provider-specific parts — only everything around them.

This resolved a policy impasse early in design and unblocked all subsequent
work. Without it, every session risks re-litigating the same question.

**Verification:** The system architecture has a clean boundary where
provider-specific extraction plugs in, with no coupling to the core.
