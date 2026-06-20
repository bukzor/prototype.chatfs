---
why:
  - canonical-conversation-graph
background:
  - har-format
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

This is provider-agnostic. Each provider maps into it via a parser (BB2):

```
.har / html / pdf / json
        |
provider parser (BB2)
        |
canonical conversation graph (extracted.json)
        |
markdown renderer (BB3)
        |
branch-main.md, branch-alt.md, ...
```

**Why graph, not linear:** Most LLM UIs internally model conversations as trees.
Linear formats lose fork history entirely. Preserving parent pointers allows
the renderer to produce per-branch markdown files.

**Already validated:** chatgpt-splat implements this for ChatGPT conversations,
confirming the data model works in practice.

**Open gap — no reasoning slot:** the fields above have no place for "thinking"
/ reasoning, and the three captured providers shape it three different ways
(claude nests it in a message's content blocks; chatgpt and aistudio externalize
it as separate nodes/turns, with different cardinality). So *where reasoning
lands in this model is a per-parser decision*, and a uniform "one response = one
unit" view must be synthesized in BB2/BB3 rather than read off the source. See
the incubator claim `chatfs-mockup-chatgpt/dev.kb/claims.kb/reasoning-turn-mapping-differs-by-provider.md`.

See also: `rotate-90-degrees-layout.md` for the on-disk representation.
