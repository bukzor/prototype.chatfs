---
why:
  - opaque-extractor-boundary
  - pipeline-composability
---

# Browse-Incidental Capture

One browse run captures more than its nominal target. We exploit this
to keep stages independent without re-browsing.

## Observation

Loading `https://chatgpt.com/c/<uuid>` in a real browser does not just
fetch the conversation document. It also populates the sidebar, which
fires `/backend-api/conversations?limit=...` — the same endpoint that
`index browse` plucks. The captured CDP stream therefore contains
*both* the conversation document and an index page that includes the
target conversation as one of its `items[]`.

## Consequence

`conversation url browse` runs both pluck filters against its single
captured CDP file:

- `chatfs-chatgpt-conversation-pluck.jq` → `$UUID.json` (the mapping
  document)
- `chatfs-chatgpt-index-pluck.jq` → filtered to `.items[] | select(.id
  == $UUID)` → `meta.json`

This makes `meta.json` deterministic from the same browse run that
fetched the conversation, with no synthesis (see
`no-partial-synthesis.md`) and no separate `index browse` prerequisite
for the common case.

## Failure mode

If the sidebar pagination did not include the target conversation
(e.g. a very old archived chat outside the first page), the index
pluck yields no matching item. The script must fail loudly rather than
fall back to synthesizing `meta.json` from the conversation document.
The user's recovery is to run `index browse` (which paginates the full
list) followed by `conversation path browse` against the resulting
ts-dir.

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
