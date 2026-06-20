---
status: observed
first-recorded: 2026-06-20
last-checked: 2026-06-20
evidence:
  - aistudio.har.jsonl  # line 426: ResolveDriveResource body, prompt 1vU6BlpV69d2MvI6L_oYGo_E-ZqmaI3eR
---

# AI Studio prompt payload is JSPB (positional arrays)

An AI Studio prompt is Drive-backed: the whole conversation arrives in a
single `ResolveDriveResource` RPC response, mime
`application/json+protobuf` (JSPB — **positional arrays, not keyed
objects**). The pluck step (`chatfs_aistudio_conversation_pluck.jq`)
emits that one decoded array; the splat reads it by field index.

The endpoint is generic (index/recents calls reuse it), so identity is
by **body shape**, not URL alone: the prompt payload is the one whose
`[0][0]` is `"prompts/<id>"`.

## Field map

Document (`body`):

| path | meaning |
|---|---|
| `[0][0]` | `"prompts/<id>"` (shape guard / id) |
| `[0][3]` | run settings; `[0][3][2]` = model slug (`models/gemini-3-flash-preview`) |
| `[0][4][0]` | title |
| `[0][4][2][0]` | author display name |
| `[0][4][4][0][0]` | created, unix seconds |
| `[0][13]` | `[live_turns, draft]` — a 2-slot pair |
| `[0][13][0]` | the live turn list |
| `[0][13][1]` | a single empty `"user"` draft turn (skip it) |

Turn (each turn is a 36-field array):

| index | meaning |
|---|---|
| `[0]` | text content (markdown) |
| `[8]` | role: `"user"` \| `"model"` |
| `[16]` | `1` on a model **answer** turn |
| `[18]` | token count |
| `[19]` | `1` on a model **thought** (reasoning) turn |

A turn is classified user / answer / thought from `[8]`/`[16]`/`[19]`;
see `chatfs_aistudio_conversation_splat.py` (`turn_kind`), which encodes
these indices as named constants and treats a model turn that is neither
answer nor thought as a parser gap (raises).

## Caveats (single capture)

- 36-field turn width and the index positions are from one prompt;
  treat as `observed`, not `settled`.
- Reasoning headers: each thought turn opens with a `**bold**` title the
  splat lifts into the disclosure `<summary>` and strips from the body.
- The thought↔answer 1:1 ratio here is not guaranteed — see
  `reasoning-turn-mapping-differs-by-provider.md`.

## Home for aistudio-specific knowledge

Per the `claude-*` precedent in this collection
(`claude-meta-field-shapes.md`, `claude-sidebar-fires-…`), provider
facts are **filename-prefixed within the shared collections**, not given
a separate `aistudio.kb/` folder. New AI Studio data-shape facts →
`claims.kb/aistudio-*.md`; new AI Studio implementation lessons →
`learnings.kb/`.
