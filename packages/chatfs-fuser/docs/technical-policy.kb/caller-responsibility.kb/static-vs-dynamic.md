---
why:
  - stateless-re-evaluation
source:
  - design-session (2026-03-20)
---

# Static vs Dynamic Directories

There is no distinction between static and dynamic directories at the type
level. `Dir` always holds a callback (`Fn() -> HashMap<String, PathSegment>`).
A "static" directory is just a callback that returns a fixed map.

Same principle as files: all files are closures, even constant ones.
