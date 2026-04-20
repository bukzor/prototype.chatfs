---
why:
  - preserve-structure
  - multi-provider
---

# Canonical Conversation Graph

All providers must map into a common tree-structured conversation format:
message IDs, parent pointers, author, content, timestamps. This format is
provider-agnostic — each provider's extraction stage (BB2) produces it.

The graph preserves forks: when a message has multiple children, the tree
branches. Downstream stages (rendering, filesystem layout) consume this
format without knowing which provider produced it.

**Verification:** A conversation with forks renders identically regardless of
which provider it came from.
