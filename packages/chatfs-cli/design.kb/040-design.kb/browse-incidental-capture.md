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
  `item["id"] == $UUID` → the sidebar's item for this chat, if any

## Which `meta.json` wins

> [!@bukzor] ruled 2026-10-12, recorded sensatim -- the four rules
> below, chosen over "sidebar if present, else disk" to minimize
> hysteresis.

- `meta.json` already on disk is used as-is.
- If the sidebar also has the chat, the two must agree, or url browse
  fails.
- If only the sidebar has it, its item is written as `meta.json`.
- If neither has it, url browse fails rather than synthesize `meta.json`
  from the conversation document (see `no-partial-synthesis.md`).

Disk wins, so the result never depends on whether the chat ranked into
this capture's sidebar page.

> [!DRAFT] agent-authored 2026-10-12, vetoable.
>
> "Agree" covers the identity fields only (id, title, creation time),
> the ones that place the chat's view. The rest of the item (update
> time, snippet) changes whenever the chat does, so comparing it would
> fail every re-capture of an active chat. url browse never refreshes
> those fields; `index browse` owns them.

Both failures are `UserError`s with one recovery: `index browse`, with
the sidebar scrolled back past the chat, then the same url browse
again. A disagreement usually means the chat was renamed since the last
index.

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
