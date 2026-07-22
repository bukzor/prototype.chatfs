---
managed-by: Skill(llm-subtask)
required-reading:
  - packages/har-browse/src/capture.mjs
suggested-reading:
  - packages/har-browse/.claude/todo.kb/2026-07-22-000-Done-Capturing-race-drops-in-flight-requests-with-no-drain.md
cost-benefit-sweh:
  timebox:
    "@value": 1.5
    rationale: |
      One `startCapture` option wired to a single CDP call
      (`Storage.clearDataForOrigin`) before `page.goto`, plus a live
      verification run per provider. No test-fixture story yet for
      "app that hydrates from IndexedDB" — live verification only for
      the first pass.
    confidence: tentative
  benefit-2w:
    "@value": 2.0
    rationale: |
      Without this, revisit captures of claude.ai conversations can
      contain zero conversation traffic — the primary BB1 payload —
      while looking like successful captures. Verified root cause of
      the 2026-07-22 a59dc891 zero-events run. Likely also affects
      index pagination (`has_more=false` symptom) and possibly other
      providers with persisted client caches.
    confidence: confident
  cost-of-delay-2w:
    "@value": 0.5
    rationale: |
      Every revisit capture taken in the interim is silently
      untrustworthy; workaround (fresh profile) forfeits login state.
    confidence: tentative
---

# claude.ai revisits render from persisted React Query IndexedDB cache, so capture sees no conversation traffic

**Priority:** High — silently produces "successful" captures with no conversation payload; the capture layer cannot fix this after the fact.
**Complexity:** Low for the mechanism (one CDP call); unknown for policy (which origins/providers, which storage types).
**Context:** Root-caused 2026-07-22 by forensics on `docs/dev/design-incubators/chatfs-cli-mockup/chatfs.demo/claude/.data/a59dc891-0f4c-4db8-8fd2-d7b679d2743d/cdp.jsonl` — the run originally misattributed to the Done-click drain race (see `2026-07-22-000-*.md`, Current Situation, for the full forensic trail).

## Problem Statement

claude.ai's document inline script persists its React Query cache to
IndexedDB (database `keyval`, object store `react-query-cache` — visible
in the captured document body). On a revisit, the conversation hydrates
from that persisted cache and **no network request for the conversation
is ever made**: the a59dc891 capture contains zero
`Network.requestWillBeSent` events matching `chat_conversation*` among
152 total, while the user watched the conversation render on screen.

The capture was *accurate* — the data genuinely never crossed the
network during the session. No amount of capture-side drain/flush work
recovers a response that was seen by client JS in a *previous* session.
"Every response the client saw this session" is the strongest invariant
CDP capture can offer; for revisits, the conversation isn't in that set.

## Current Situation

- First visit to a conversation: page fetches `/chat_conversations/{uuid}`
  → captured fine (the 2026-07-22 first run demonstrated this).
- Revisit with the same persistent profile: hydrates from IndexedDB,
  zero conversation events, capture looks successful but is empty of
  payload.
- Persistent profiles are load-bearing (login state), so "fresh profile
  per capture" is not an acceptable fix.

## Proposed Solution

Clear app-level storage for the target origin *before* navigation, so
the app is forced to re-materialize its data as network traffic:

- Add a `startCapture` option (e.g. `clearOriginStorage: true`) that,
  after CDP attach but before `page.goto`, issues
  `Storage.clearDataForOrigin { origin, storageTypes: "indexeddb" }`.
- Keep cookies (login) untouched. Start with `indexeddb` only; widen to
  `cache_storage`/`local_storage` only if a provider proves to hydrate
  from those too.
- Wire the flag through `har_browse.mjs` CLI (`--clear-origin-storage`?)
  and default it ON for the chatfs provider flows.

Alternative considered: extract the conversation directly from the
persisted cache via CDP `IndexedDB.requestData` — the cache *is* the
data. Rejected for now: changes the BB1 contract from "CDP network
events" to "CDP network events + IndexedDB dumps"; keep the pipeline
shape, force the traffic instead.

## Implementation Steps

- [ ] Add `clearOriginStorage` to `startCapture` (CDP
      `Storage.clearDataForOrigin`, indexeddb only, pre-goto)
- [ ] Expose via `har_browse.mjs` CLI flag
- [ ] Live verification per provider: a claude.ai revisit capture now
      contains `chat_conversation*` rWBS + RR with body; same forensic
      grep on chatgpt + aistudio revisit captures checks them for
      equivalent persisted-cache hydration
- [ ] Burn down the 4 `status: todo` mutation-testing.kb entries pre-filed 2026-07-22 for this feature. Two test constructions cover all four: the hydrating fixture (toy-server page: fetch-and-store-to-IndexedDB on first load via *inline parse-time script*, render-from-IndexedDB-without-fetching on revisit; assert the second capture under `clearOriginStorage: true` contains the payload rWBS + RR) kills `clear-origin-storage-call-removed.md`, `clear-origin-storage-after-goto.md`, `clear-origin-storage-wrong-origin.md`; a cookie-survival assertion kills `clear-origin-storage-types-include-cookies.md`. The hydrating fixture doubles as this todo's regression test. (Whether this todo also owns the incubator's `has_more=false` symptom is decided by the discriminator step — first step — of `2026-07-22-000-*`.)

## Open Questions

- Does React Query revalidate the persisted entry in the background
  eventually (stale-while-revalidate)? If yes, "wait longer before
  Done" might also capture the traffic — worth one observation run,
  since it bounds how much we care about clearing vs. waiting.
- Which origin(s) to clear for claude.ai (claude.ai vs api CDN
  origins)? IndexedDB is origin-scoped; the `keyval` db lives on
  `https://claude.ai`.
- Should clearing be per-provider policy (chatfs side) rather than a
  har-browse default? har-browse provides the mechanism either way.

## Success Criteria

- [ ] Two consecutive captures of the same claude.ai conversation with
      the same profile both contain the conversation response body in
      the CDP stream
- [ ] Login state survives (no re-auth needed on the second capture)

## Notes

Sibling todo `2026-07-22-000-*` (drain race) is a real but independent
bug — the same forensic pass found exactly 2 rWBS-without-RR victims in
the a59dc891 capture (`api.anthropic.com/api/directory/servers` fetches
in flight at click). Both fixes are needed; neither substitutes for the
other.
