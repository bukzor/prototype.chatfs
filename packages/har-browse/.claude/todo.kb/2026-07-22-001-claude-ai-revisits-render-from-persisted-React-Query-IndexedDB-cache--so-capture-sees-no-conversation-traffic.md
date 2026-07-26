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
  `Storage.clearDataForOrigin { origin, storageTypes: "indexeddb,cache_storage" }`.
  *(Widened 2026-07-23: Cache Storage is the same never-requested gap
  class — a service worker's cache-first handler serves payload without
  network traffic — and clearing it is equally cheap and login-safe.)*
- Keep cookies (login) untouched. `local_storage` stays opt-in per
  provider, not default: some providers keep auth tokens there, and
  clearing would forfeit the login state persistent profiles exist to
  preserve. Verify login survives before enabling it anywhere.
- Session-level capture settings (same "force client state through the
  observable network" motive, applied per CDP session at wire-up rather
  than per origin): `Network.setCacheDisabled(true)` (standard for HAR
  tooling — full bodies instead of cache hits with occasionally
  unfetchable bodies) and `Network.setBypassServiceWorker(true)`
  (fetches go network-direct, converting most service-worker-mediated
  traffic into ordinary page-session events without touching the
  profile — interim mitigation for `2026-07-23-001-*`'s non-page-target
  gap).
- Wire it through the `har_browse.mjs` CLI and default it ON. *(Landed
  2026-07-26 as an opt-out flag, `--keep-origin-storage`.)*

Alternative considered: extract the conversation directly from the
persisted cache via CDP `IndexedDB.requestData` — the cache *is* the
data. Rejected for now: changes the BB1 contract from "CDP network
events" to "CDP network events + IndexedDB dumps"; keep the pipeline
shape, force the traffic instead.

## Implementation Steps

- [x] Add `clearOriginStorage` to `startCapture` (CDP
      `Storage.clearDataForOrigin`, indexeddb + cache_storage, pre-goto;
      local_storage left out)
- [x] Apply per-session capture settings in `wireSession`:
      `Network.setCacheDisabled(true)`,
      `Network.setBypassServiceWorker(true)`
- [x] Expose via `har_browse.mjs` CLI flag (`--clear-origin-storage`)
- [x] Live verification on claude.ai — done 2026-07-26, five human-driven
      captures against the real site (`trash/live-verify/`, devlog
      `2026-07-26-002`). The bug reproduces today and the flag fixes it;
      see Live Verification below for the run matrix and the two
      corrections it forced.
- [ ] Same forensic grep on chatgpt + aistudio revisit captures, to see
      whether they hydrate equivalently. Batched 2026-07-26 into
      todo.md's live `--howto` session (request it per CLAUDE.md
      Protocols); must cold-load each conversation's own URL, per the
      run-1 correction below.
- [x] Burn down the 4 pre-filed mutation-testing.kb entries, all now
      `status: done`. Two new entries cover the session settings
      (`session-cache-not-disabled`,
      `session-service-worker-not-bypassed`). Local coverage is
      `tests/clear_origin_storage.spec.mjs` (4 tests) and
      `tests/session_settings.spec.mjs` (2), on `/hydrate`, `/cacheable`
      and `/sw-page` fixtures in `tests/_common/server.mjs`; every
      mutation was confirmed red. `clear-origin-storage-wrong-origin`'s
      predicted kill was wrong — see that entry: a `"null"` origin (what
      `about:blank` serializes to) makes CDP clear *every* origin, so
      the defect is scope and the test asserts a bystander origin
      survives.

## Open Questions

- Does React Query revalidate the persisted entry in the background
  eventually (stale-while-revalidate)? If yes, "wait longer before
  Done" might also capture the traffic — worth one observation run,
  since it bounds how much we care about clearing vs. waiting.
- Which origin(s) to clear for claude.ai (claude.ai vs api CDN
  origins)? IndexedDB is origin-scoped; the `keyval` db lives on
  `https://claude.ai`.
- ~~Should clearing be per-provider policy (chatfs side) rather than a
  har-browse default?~~ **Resolved 2026-07-26: har-browse default.**
  This was the plan in Proposed Solution all along ("default it ON for
  the chatfs provider flows"); the live runs made the cost of getting
  it wrong concrete -- a capture that looks fine and holds none of its
  payload. The CLI clears unless given `--keep-origin-storage`.
  `startCapture` keeps the option defaulting off: the primitive does
  what it is asked, the flow protects the human. Both directions pinned
  by `tests/cli_clear_default.spec.mjs`.

## Success Criteria

- [x] Two consecutive captures of the same claude.ai conversation with
      the same profile both contain the conversation response body in
      the CDP stream — runs 4 and 5, both `200` with a 198115-byte body,
      byte-identical in length.
- [x] Login state survives (no re-auth needed on the second capture) —
      no login/auth navigation in either run, and an authenticated `200`
      carrying real conversation content is itself the proof.

## Live Verification (2026-07-26)

One conversation, one persistent profile (`default_profile`), five
captures. Conversation-request counts:

| run | build | `--clear-origin-storage` | entered via | conversation requests |
|-----|-------|--------------------------|-------------|----------------------|
| 1 | fixed | no | Recents, then clicked in | 1 (198115-byte body) |
| 2 | pre-fix (`fb60208^`) | n/a | cold load of the chat URL | **0** |
| 3 | fixed | no | cold load | **0** |
| 4 | fixed | **yes** | cold load | 1 (198115-byte body) |
| 5 | fixed | **yes** | cold load | 1 (198115-byte body) |

Run 2 is the reproduction: the human watched the conversation render
while the capture recorded no request for it. Runs 4 and 5 are the fix.
The human also reported run 4 loading visibly slower than the hydrating
runs, which is the mechanism made observable.

Two corrections this forced:

1. **The per-session settings do not fix this.** Run 3 has
   `setCacheDisabled` and `setBypassServiceWorker` and still captures
   zero conversation traffic. Neither capture showed a single
   `requestServedFromCache` event or a `fromServiceWorker` response, so
   for claude.ai they address neither path. They remain justified for
   the gap classes they target, but they are unvalidated live and must
   not be described as covering this bug.
2. **Run 1 fetched for an unrelated reason.** It entered the
   conversation by clicking through from Recents -- a client-side route
   change, which fetches regardless. Only a cold load of the
   conversation URL exercises the parse-time hydration path. Any future
   verification must cold-load the URL, or it measures nothing.

Follow-on: entering via Recents sidesteps the bug, so a capture
workflow that always navigates in from the list is incidentally safe.
That is a fragile property to rely on -- it depends on claude.ai's
routing -- but it explains why this was not noticed sooner.

## Notes

Sibling todo `2026-07-22-000-*` (drain race) is a real but independent
bug — the same forensic pass found exactly 2 rWBS-without-RR victims in
the a59dc891 capture (`api.anthropic.com/api/directory/servers` fetches
in flight at click). Both fixes are needed; neither substitutes for the
other.
