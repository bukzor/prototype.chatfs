---
why:
  - deterministic-output
  - content-encoding-handling
---

# Conversation Graph Fixture

The toy backend's `/api/conversation` endpoint returns a small, fixed
conversation graph with:

- Message IDs and parent pointers (tree structure)
- At least one fork (two children of the same parent)
- Timestamps (fixed, not generated)
- Enough messages to produce two distinct branches (`branch-main.md`,
  `branch-alt.md`)

This fixture is the "known answer" that makes the entire pipeline
deterministically testable. The `/api/large` endpoint adds a larger payload
for compression and streaming testing.
