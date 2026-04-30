---
why:
  - opaque-extractor-boundary
  - canonical-conversation-graph
---

# No Partial Synthesis of Provider Structures

Files that mirror provider data structures are written whole or not at
all. We do not synthesize partial versions from whatever we happen to
have on hand.

## Rule

If a stage cannot produce the complete structure of a file from
captured provider data, it must not produce a partial one. Either:

1. **Capture more** so the structure can be written whole, or
2. **Normalize the schema** so what *can* be written is the entire
   schema (i.e., the schema only contains fields the stage actually
   has), or
3. **Fail loudly.**

## Why

`meta.json` is the motivating case. The index endpoint
(`/backend-api/conversations?...`) returns rich per-conversation
records: `id`, `title`, `create_time`, `update_time`, `is_starred`,
`gizmo_id`, and more. The conversation endpoint
(`/backend-api/conversation/{id}`) has its own top-level fields with
some overlap.

It is tempting, when capturing a single conversation by URL, to
synthesize a "minimal" `meta.json` from the conversation document
alone. Doing so silently produces a `meta.json` whose schema differs
from the index-splat-produced one — same filename, different shape.
Downstream stages then either tolerate the difference (and silently
read fewer fields) or fail at a distance from the synthesis site.

The corollary is: **don't lie about file shape with the filename.** If
two stages can only ever produce different schemas, they should not
share a filename.

## Practical guidance

- `meta.json` is exactly the shape of one entry in the index endpoint's
  `items[]` array. Anything writing `meta.json` must produce that shape
  byte-for-byte (modulo formatting).
- The browse-incidental-capture decision (sibling entry) is what makes
  this rule cheap to follow for `conversation url browse`: the index
  endpoint fires anyway during the conversation page load.
- If a future flow legitimately has only partial data, give the partial
  artifact a different filename (e.g. `meta.partial.json`) and document
  the schema explicitly.
