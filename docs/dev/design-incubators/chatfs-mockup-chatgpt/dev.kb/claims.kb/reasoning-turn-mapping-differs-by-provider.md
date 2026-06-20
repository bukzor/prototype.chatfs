---
status: observed
first-recorded: 2026-06-20
last-checked: 2026-06-20
evidence:
  - chatfs.demo/claude/.chat/8ca43a18-f002-4916-af92-c77256c82617/.data/conversation.json  # thinking nested in message content[]
  - chatfs.demo/chatgpt/.chat/69de8f14-e80c-8329-b3a8-3e4046c10cb1/.data/conversation.json  # thoughts/reasoning_recap as separate mapping nodes
  - aistudio.har.jsonl  # thoughts as separate turns ([19]=1)
---

# Reasoning↔turn mapping differs by provider

How a provider's source data relates **reasoning** ("thinking") to the
**turn/message** that carries the answer is structurally different in
all three providers we've captured. There is no shared shape to inherit.

| provider | container | where reasoning lives | cardinality |
|---|---|---|---|
| claude | flat `chat_messages[]` | a `thinking` **block inside** the assistant message's `content[]`, interleaved with `text`/`tool_use` | **intra-turn** — one message bundles thinking + answer + tools |
| chatgpt | `mapping` **tree** of nodes | **separate nodes**: `content_type:"thoughts"` *and* a distinct `reasoning_recap`, siblings of the `text` answer node | **many-per-response** — several thoughts nodes + a recap precede one answer |
| aistudio | flat turn list `[0][13][0]` | **separate turns** (`role:model`, `[19]==1`), sibling to the answer turn (`[16]==1`) | **1:1 in this capture** — one thought turn per answer turn; not guaranteed by the format |

## Why it matters

The canonical conversation graph
(`docs/dev/design.kb/040-design.kb/canonical-conversation-graph.md`)
models `message_id / parent_id / author / content / timestamp` — it has
**no slot for reasoning**. Each provider parser (BB2) must decide where
"thinking" lands in that model, and the source data points three
different ways:

- **claude nests** → the splat folds thinking into the answer's `.md`
  (one file per assistant message).
- **aistudio externalizes 1:1** → the splat emits a separate
  `NNN.model.thought.md`, and the answer is a *different* file.
- **chatgpt externalizes many-to-one** (+ a second `reasoning_recap`
  kind) → a future splat would emit several reasoning units per answer.

Consequence: "the assistant's response to prompt N" is **one file** on
the claude side but **two** on the aistudio side, and would be **several
nodes** on a chatgpt splat. A uniform "one response = one unit" view, if
ever wanted, must be **synthesized in splat/render** — the source data
will not give it for free.

## See also

- `aistudio-jspb-prompt-shape.md` — the field indices behind the
  aistudio column.
- `learnings.kb/path-render-shape-is-provider-shaped.md` — same flavor
  of "provider-shaped, not provider-specific" finding for `path_render`.
- Project design: `040-design.kb/canonical-conversation-graph.md` (the
  reasoning-slot gap noted there points back here).
