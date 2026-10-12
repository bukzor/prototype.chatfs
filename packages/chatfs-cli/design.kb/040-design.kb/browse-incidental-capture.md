---
why:
  - ../../../../docs/dev/design.kb/030-requirements.kb/opaque-extractor-boundary.md
  - ../../../../docs/dev/design.kb/030-requirements.kb/pipeline-composability.md
---

# Browse-Incidental Capture

One browse run captures more than its nominal target. We exploit this
to keep stages independent without re-browsing.

## Observation

Loading `https://chatgpt.com/c/<uuid>` in a real browser does not just
fetch the conversation document. It also populates the sidebar, which
fires `/backend-api/conversations?offset=0&limit=28&order=updated&is_archived=false&is_starred=false`
— the same endpoint that `index browse` plucks. The captured CDP stream
therefore contains *both* the conversation document and the sidebar's
first page. That page includes the target only when the target is
among the 28 most recently updated, unstarred chats: nothing adds the
open chat to it. Across the 55 chatgpt captures on hand (2026-10-12),
inclusion matched that prediction 55/55, and 44 did not include their
target.

## Consequence

`conversation url browse` runs both plucks against its single captured
CDP file, placing the outputs in `.data/$UUID/`:

- `chatfs.provider.chatgpt.pluck.pluck_conversation` →
  `conversation.json.d/raw.jsonl` → assemble →
  `conversation.json` (see `conversation-document-is-whole.md`)
- `chatfs.provider.chatgpt.pluck.pluck_index_pages` → filtered to
  `item["id"] == $UUID` → `meta.json`

This makes `.data/$UUID/meta.json` deterministic from the same browse
run that fetched the conversation, with no synthesis (see
`no-partial-synthesis.md`) and no separate `index browse` prerequisite
for the common case.

## Failure mode

If the sidebar page did not include the target conversation (any
chat outside the first page), the index pluck yields no matching
item. The script must fail loudly rather than
fall back to synthesizing `meta.json` from the conversation document.
The user's recovery is `conversation path browse`, preceded by
`index browse` (with the sidebar scrolled back past the chat) if no
earlier index placed its `meta.json`.

## Why not always require `index browse` first

It would be simpler to mandate "always run `index browse` before
`conversation * browse`." We don't, because:

- The single-URL flow is the common ad-hoc case (someone shares a
  link; the user wants to capture that one chat).
- The browse already happens; re-using its bycatch is free.
- Requiring two browse runs for one conversation doubles latency and
  Chromium overhead for no incremental data.

The fallback to `index browse` exists for the long-tail case, not the
common case.
