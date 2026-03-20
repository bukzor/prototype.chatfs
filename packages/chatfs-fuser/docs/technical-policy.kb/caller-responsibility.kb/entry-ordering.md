---
why:
  - stateless-re-evaluation
source:
  - design-session (2026-03-20)
---

# Entry Ordering

`readdir` returns entries in the order the caller's `Dir` callback provides
them (via HashMap iteration order, which is arbitrary). Callers who need
sorted output should sort in their callback.
