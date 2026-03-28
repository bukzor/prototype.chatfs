---
why:
  - no-network-on-read
  - explicit-sync-triggers
source:
  - conversations.cleaned/04-system-decomposition-sync-design/133.assistant.text.md
  - conversations.cleaned/06-design-spec-project-handoff/167.assistant.text.md#4
---

# No Expensive Work on read()

All filesystem read operations (and JSONL layer reads) serve from cache or
in-memory state. No network requests, no subprocess invocations, no file
generation during reads.

This is the most load-bearing invariant. It makes the system safe to use with
editors, ripgrep, shell completion, and file watchers — all of which generate
rapid, speculative filesystem operations. If reads triggered network activity,
the system would be unusable.

Refresh is always an explicit, user-initiated action: `touch`, control file
write, or CLI command.
