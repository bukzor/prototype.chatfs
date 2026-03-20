---
why:
  - stateless-re-evaluation
source:
  - design-session (2026-03-20)
---

# dir_each Composition

`FilesystemBuilder::dir_each` is a convenience method, not a primitive.
It composes over `.dir()` — calling `list_fn()` at build time and adding
one `.dir()` per item. The implementation is ~15 lines of pure composition.

For truly dynamic directories (children evaluated on each access, not at
build time), construct a `PathSegment::Dir` directly with a closure that
returns fresh children each call. See the `procfs` example.
