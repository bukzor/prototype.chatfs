---
status: assumed
first-recorded: 2026-05-12
last-checked: 2026-05-12
evidence:
  - claude.chat.b0f46746-e087-44de-9d34-ce0e15027d6b.jsonl  # zero _v2 hits, plausibly truncated
---

# claude.ai's sidebar fires `/chat_conversations_v2` on chat pages

When the browser loads `https://claude.ai/chat/$UUID`, the persistent
sidebar fetches the same `/chat_conversations_v2?…` endpoint it uses
on `/recents`. The page that mentions $UUID will therefore be
captured incidentally by har-browse, available for pluck under the
existing index pluck filter.

## Why it matters

`chatfs_claude_conversation_url_browse.py` relies on this: one browse
trip captures both the conversation document and the sidebar index
page mentioning the target UUID. If the sidebar doesn't fire `_v2`,
url_browse fails loud via `find_index_item`, and the user falls back
to the two-step recovery (`index_browse.sh | index_splat.py` →
`conversation_path_browse.py`).

## Evidence so far

**Inconclusive.** The one captured chat CDP
(`claude.chat.b0f46746-…jsonl`) shows zero `chat_conversations_v2`
requests, but that capture is plausibly truncated — known symptom:
pressing "Done Capturing" before the sidebar's initial fetch yields a
CDP missing those events. See sibling claim
`har-browse-cdp-may-trail-visual-interactability.md`.

The assumption stands until a deliberately slow capture either
confirms (`_v2` appears) or refutes it (long-idle capture still
shows zero `_v2`).

## How this settles

- First real `url_browse` invocation against a fresh URL is the test.
- If assertions pass → status: observed. Repeat across several chats
  to reach `settled`.
- If `find_index_item` raises → status: refuted; file a clarification
  and move url_browse to a different design (e.g. two-trip, or
  fallback to conversation-doc-derived meta).
