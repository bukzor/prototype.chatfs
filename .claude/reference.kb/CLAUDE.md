# reference.kb/ — stable external pointers

## What belongs

Canonical paths and URLs that other facts cross-link to. External
specifications, source-of-truth files in other repos, project-internal
data files, and standard commands. One file per pointer.

The role is to let other kb files reference a single stable location
instead of repeating the path inline.

## What does NOT belong

- **Content** that lives elsewhere — `reference.kb/` files point at
  things, they don't reproduce them.
- **Decisions** or **observations** that depend on the reference —
  those go in their own kbs and link here.
- **Ephemeral URLs** (PR comments, ticket threads) — only durable
  references.

## When to add

When two or more other kb files would otherwise hardcode the same
path/URL, OR when a single pointer is important enough to call out
explicitly (canonical standard, source-of-truth file).
