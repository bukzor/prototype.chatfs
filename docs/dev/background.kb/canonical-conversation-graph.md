---
source:
  - conversations.cleaned/06-design-spec-project-handoff/167.assistant.text.md#1
---

# Canonical Conversation Graph Format

Conversations are modeled as trees with forks, not linear sequences. The
canonical format preserves:

- `message_id` — stable identifier
- `parent_id` — tree structure
- `author` — human / assistant / system
- `content` — message text
- `timestamp` — when created

This is provider-agnostic. Each provider maps into it via a parser:

```
.har / html / pdf / json
        ↓
provider parser (BB2)
        ↓
canonical conversation graph (extracted.json)
        ↓
markdown renderer (BB3)
        ↓
branch-main.md, branch-alt.md, ...
```

**Why graph, not linear:** Most LLM UIs internally model conversations as trees.
Linear formats lose fork history entirely. Preserving parent pointers allows
the renderer to produce per-branch markdown files.

**Already validated:** chatgpt-splat implements this for ChatGPT conversations,
confirming the data model works in practice.

See also: `rotate-90-degrees-layout.md` for the on-disk representation.
