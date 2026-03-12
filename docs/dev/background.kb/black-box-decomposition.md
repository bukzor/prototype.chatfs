---
source:
  - conversations.cleaned/04-system-decomposition-sync-design/127.assistant.text.md
  - extracted/04-bb-decomposition.md
---

# Black Box Decomposition (BB1 / BB2 / BB3)

The capture-to-rendering pipeline is decomposed into three opaque components:

- **BB1 (capture):** Given a conversation reference, produces a capture artifact
  (HAR, trace, or similar). Involves browser automation and network interception.
- **BB2 (pluck):** Consumes the capture artifact, outputs structured
  conversation data (`extracted.json`) — messages, IDs, parent pointers,
  timestamps, branches.
- **BB3 (emit):** Consumes structured data, writes rendered files (`.md`) and
  metadata into an output directory.

**Conceptually:** Three logical phases of extraction.
**Operationally:** May be one CLI command or three. Each sync invocation is
short-lived with clean failure semantics — no long-running agent.

The rest of the system (daemon, cache, filesystem, orchestration) only depends
on stable I/O: command invocation, exit codes, file paths, atomic outputs.
Providers can swap BBs without touching the core.

**Full text:** [data/todo-llmfs.chatgpt.com.splat/extracted/04-bb-decomposition.md]
