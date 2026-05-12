# 2026-05-12: chatfs-mockup-chatgpt — claude entry-point parity

## Focus

Land the four remaining claude-side scripts to match the chatgpt-side
entry-point surface: `conversation_path_browse`, `conversation_url_render`,
`conversation_url_browse`, and `index_browse.sh`.

## What Happened

**Three of the four were mechanical mirrors** of their chatgpt
siblings — same shape, swap layout/pluck imports, swap URL scheme
(`/c/{uuid}` → `/chat/{uuid}`), swap UUID field (`id` → `uuid`). Each
ran pyright-clean on first compose.

**`url_browse` raised a real design question.** The chatgpt one-trip
pattern relies on browse-incidental capture: visiting `/c/$UUID` also
fires the sidebar's `/backend-api/conversations` index pages, which
`find_index_item` filters to extract canonical meta. I asserted from
the existing CDP capture (`claude.chat.b0f46746-…jsonl`) that visiting
`/chat/$UUID` does **not** trigger `chat_conversations_v2` — zero
network events under that URL prefix; the lone string-match was a JS
bundle body. User pushed back: the sidebar should share the same
endpoint as `/recents`. The existing capture is plausibly truncated
(it's MVP-era and may have been stopped before the sidebar got around
to its initial fetch — the known "Done Capturing too early" symptom).

**User chose option D: assume-and-assert.** Implement the one-trip
pattern (assume `_v2` fires); if `find_index_item` returns no match,
fail loud with the two-step recovery path. Add a null-tolerant
cross-check between the conversation doc's overlapping fields and the
index item — catches schema drift in either endpoint. This guard
exists only on the claude side; chatgpt's `url_browse` doesn't have
it yet but could.

**Field-shape comparison.** Index endpoint exposes 15 keys; conversation
endpoint exposes 11. The four extras are `project_uuid`, `session_id`,
`user_uuid`, `project` — all null in the test data. The
null-tolerant assertion ignores key absence and null on either side,
so non-project chats pass; project chats with non-null project_* on
index but null on conversation also pass (because the conversation
side is null).

**Not tested live.** `index_browse.sh` and `url_browse.py` both need
an interactive browser session. Replay-testing `url_browse`'s pluck
side against the existing partial CDP would fail loud (as designed —
no `_v2` page → `find_index_item` raises), so it's not a useful
regression test. The real verification is a fresh slow capture
against a live URL — first invocation tells us whether the
browse-incidental assumption holds.

## Lessons

**Empirical claims about live behavior need empirical evidence, not
single-file inference.** I'd inferred "sidebar doesn't fire on chat
pages" from one CDP file. That file was made during MVP work and may
itself be truncated. Single-sample inference about external service
behavior is brittle; the right discipline is to flag the assumption,
gate it behind an assertion, and let real-world runs settle it.

**Two providers expose where shared-code refactor will start.** The
moves are now obvious: `uuid_from_url` (provider-specific URL path),
`find_index_item` (provider-specific item-key + path-pattern),
`null_tolerant_mismatches` (provider-agnostic). The shape of a
hypothetical `chatfs_browse.py` core is starting to emerge — but
it'd be premature to extract from two samples; user-flagged
"shared code among providers" todo correctly waits for provider three.

**Assume-and-assert is the right shape when divergence is the
interesting outcome.** Option D dominates option C (two-step UX) on
two axes: (a) UX-symmetric with chatgpt, (b) the first failure
generates a documented data point about claude.ai's behavior. The
cost is one branch in the recovery code; the benefit is empirical
discovery on the path that always runs.

## Next Session

- **Live URL test of `url_browse`** against a fresh claude chat —
  the empirical settler for the browse-incidental assumption. If it
  fails, the recovery path (`index_browse | index_splat` →
  `path_browse`) is already in place and tested by replay.
- **Live `index_browse.sh` test** — exercises the existing pipeline
  end-to-end against `/recents`; surfaces the "Done Capturing
  timing" symptom in a real workflow.
- **Branches in splat** (`conversations/<branch>.md`) — render side
  already groups dead branches; splat-side enumeration makes them
  navigable from the chat dir root.
- **Rich content blocks** — thinking, tool_use, tool_result render
  paths; current MVP captures all four block types so it's
  shovel-ready.
