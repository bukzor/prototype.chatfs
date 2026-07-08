---
force: should
why:
  - provider-agnostic-interface
source:
  - user (bukzor)
---

# Normalize Into Invariants, Not Callbacks

When a shared core holds a strong invariant that some inputs legitimately
violate, repair the input into the invariant at the boundary rather than
threading per-source callbacks through the core. Data IR over hooks: the
repaired input is inspectable, diffable, and testable pure.

Instance: `chatfs_render.py` requires every non-root node to carry a turn;
chatgpt repairs its turn-less nodes via `normalize_turnless` up front rather
than the renderer accepting provider callbacks.
