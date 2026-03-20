---
why:
  - stateless-re-evaluation
source:
  - docs/design-incubators/dynamic-routing/CLAUDE.md
---

# Parameter Threading

The framework does not thread parent path segments to child callbacks.
Callers capture what they need via closures.

A routing-style framework (cf. FastAPI Depends, Axum extractors) could
automate this. Deferred — closures work fine at current complexity.
