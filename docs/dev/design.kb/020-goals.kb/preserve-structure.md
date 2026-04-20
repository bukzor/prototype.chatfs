---
why:
  - chatfs
---

# Preserve Conversation Structure

LLM conversations are trees, not flat transcripts. Most providers support
forking (editing a message to explore an alternative branch). Flattening
to linear text loses this structure permanently.

chatfs should preserve the full tree: message IDs, parent pointers, fork
points, and branch paths. The on-disk and filesystem representations should
make forks visible and navigable.
