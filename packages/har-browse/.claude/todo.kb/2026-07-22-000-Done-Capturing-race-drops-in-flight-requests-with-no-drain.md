---
managed-by: Skill(llm-subtask)
required-reading:
  - packages/har-browse/src/capture.mjs
suggested-reading:
  - docs/dev/mutation-testing.kb/body-fetch-not-tracked.md
  - docs/dev/mutation-testing.kb/done-finally-skips-inflight-drain.md
  - docs/dev/mutation-testing.kb/context-close-no-stream-end.md
  - tests/popup_race.spec.mjs
cost-benefit-sweh:
  timebox:
    "@value": 2.0
    rationale: |
      Two small, localized diffs in capture.mjs (in-flight tracking
      extension + grace-period timeout), sketched already. Remaining
      cost is mostly the regression test (constructing a genuinely slow
      pending-response fixture), deferred to the user.
    confidence: tentative
  benefit-2w:
    "@value": 0.8
    rationale: |
      Silent, undetected data loss on any live capture across all three
      chatfs providers (claude/chatgpt/aistudio) whenever a human clicks
      "Done Capturing" before a slow request finishes — no error, no
      partial record, just an absent response. Demonstrated in the
      a59dc891 capture itself: exactly 2 requests with rWBS but no RR
      (both api.anthropic.com/api/directory/servers, in flight at
      click). NOTE 2026-07-22 later analysis: the originally-motivating
      symptom (zero conversation events) is NOT this bug — see Current
      Situation; benefit revised down accordingly.
    confidence: verified (bug + in-capture instances); original symptom re-attributed
  cost-of-delay-2w:
    "@value": 0.3
    rationale: |
      No external deadline; the bug is intermittent/timing-dependent
      and has a known manual workaround (wait longer before clicking
      Done, or recapture). Low but nonzero — silent failures erode
      trust in captures until root-caused.
    confidence: tentative
---

# Done Capturing race drops in-flight requests with no drain

**Priority:** Medium — silent data loss, no error surfaced; timing-dependent so easy to miss.
**Complexity:** Low-Medium — fix is localized to `capture.mjs`; the hard part is constructing a regression test for the race window, not the fix itself.
**Context:** Discovered 2026-07-22 during the chatfs-cli-mockup module-shape-refactor's deferred "live end-to-end run" verification (see `docs/dev/design-incubators/chatfs-cli-mockup/.claude/todo.kb/2026-07-13-000-graduation-and-integration.kb/2026-07-13-000-module-shape-refactor.md`'s Success Criteria). A live `claude.provider.conversation.url_browse` capture, run twice against the same real conversation, produced a `cdp.jsonl` with **zero** `/chat_conversations/{uuid}` or `/chat_conversations_v2` events on the second run — not even headers-only, nothing — despite the user seeing the conversation content render on screen before clicking "Done Capturing" fairly quickly. *(2026-07-22, later analysis: that specific symptom was subsequently re-attributed — see Current Situation. Kept here as discovery history.)*

## Problem Statement

`har-browse`'s `attachCapture()` in `src/capture.mjs` only guarantees that requests which have *already reached* `Network.loadingFinished` by the time "Done Capturing" is clicked get drained before the stream closes (the `inFlight` set is populated inside the `loadingFinished` handler, wrapping the async `getResponseBody` call — see `body-fetch-not-tracked.md` / `done-finally-skips-inflight-drain.md`, both already mutation-tested and gated by `tests/popup_race.spec.mjs`). A request that's been *sent* but hasn't reached `loadingFinished` yet at click time (still downloading, or the server just hasn't answered) has **no tracker anywhere** — the drain doesn't wait for it, `context.close()` kills it, and it vanishes with zero trace in the output (worse: `Network.responseReceived`'s handler doesn't even enqueue headers — that only happens inside `onLoadingFinished` — so there's no partial record either).

This is a strictly earlier/wider gap than anything the existing mutation-testing.kb entries in this area cover — those all assume the request already reached the post-`loadingFinished` body-fetch step by click time.

## Current Situation

The bug is confirmed in source (not yet fixed) — but forensics on the actual capture (2026-07-22, `docs/dev/design-incubators/chatfs-cli-mockup/chatfs.demo/claude/.data/a59dc891-0f4c-4db8-8fd2-d7b679d2743d/cdp.jsonl`) show the motivating zero-conversation-events symptom is **not** this bug:

- The capture contains **zero** `Network.requestWillBeSent` matching `chat_conversation*` (152 rWBS total; the only whole-file matches for that string are inside JS-bundle response bodies). The drain race cannot produce that signature — rWBS flows through the passthrough branch and is emitted immediately; only the response side is droppable. Its true signature is rWBS-present-with-RR-absent.
- The conversation was never fetched: the captured document's inline script persists claude.ai's React Query cache to IndexedDB (db `keyval`, store `react-query-cache`), and the revisit hydrated from it. The capture accurately recorded a session in which the conversation never crossed the network. That failure mode is tracked separately in `2026-07-22-001-claude-ai-revisits-render-from-persisted-React-Query-IndexedDB-cache--so-capture-sees-no-conversation-traffic.md`.
- The drain race **is** present in the same capture, with different victims: exactly 2 requests have rWBS but no `responseReceived` — both `api.anthropic.com/api/directory/servers` fetches in flight at click time. Bug real; original victim misattributed.

The `has_more=false` linkage is therefore also suspect: persisted-cache hydration explains "missing later index pages" at least as well as the drain race. Discriminator, checkable against existing captures before any fix lands: index-page URL has rWBS but no RR → drain race; no rWBS at all → cache hydration (or never requested).

## Proposed Solution

Three changes, must land together:

1. **Extend in-flight tracking to the full request lifecycle.** Currently tracking starts at `loadingFinished`. Add a new `pendingRequests: Map<requestId, resolve>` populated at `Network.requestWillBeSent` (earliest CDP signal), with a `track()`ed promise per request; resolve-and-delete it from both `onLoadingFinished` and `onLoadingFailed`. Guard against redirects re-firing `requestWillBeSent` with the same `requestId` (only create a tracker if one doesn't already exist for that id) so a single logical request isn't double-tracked/orphaned across redirect hops. `requestWillBeSent` isn't currently a special-cased handler (it flows through the generic passthrough branch) — the new handler must keep re-enqueueing it raw, same as today.

2. **Bound the drain with a grace-period timeout.** Fix 1 alone means a request that *never* reaches a terminal event (truly hung, or the CDP session dies mid-flight) blocks `inFlight` forever — and since the caller only calls `context.close()` *after* the events stream ends, that's a genuine deadlock (nothing left to abort the hung request). Wrap the final drain in `Promise.race([Promise.allSettled([...inFlight]), timeout(DRAIN_GRACE_MS)])` so shutdown is bounded. `DRAIN_GRACE_MS` (sketched at 2000) is a guessed constant, not derived — open question below. Two consequences to design around: (a) never-finishing requests are *normal*, not exceptional — the a59dc891 capture holds an open EventSource (`mcp/v2/bootstrap`), so with fix 1 every capture pays the full grace period; keep it modest. (b) On the window-close (cancel) path the context is dying and no terminal events will ever arrive — grace there is pure added latency; consider skipping it.

3. **Flush, don't drop, at grace expiry.** When the grace period ends with requests still outstanding, emit their stashed `Network.responseReceived` params (headers, no body) with an explicit truncation marker (e.g. `params.response.harBrowseTruncated = true`) instead of discarding `awaitingBody` silently. This converts invisible loss into a grep-able signature — the misattribution documented in Current Situation happened precisely because drops leave no trace in the output.

Full code-level sketch (diffs against current `capture.mjs`) was worked out in the 2026-07-22 conversation that produced this file but is not reproduced here in detail — regenerate by re-reasoning from the Proposed Solution above plus the file's current shape; it's a small, mechanical extension of the existing `awaitingBody`/`inFlight`/`track()` pattern, not a redesign.

## Implementation Steps

- [ ] Implement fix 1 (`pendingRequests` map + `requestWillBeSent` handler + resolve calls in `onLoadingFinished`/`onLoadingFailed`)
- [ ] Implement fix 2 (bounded-timeout drain, `DRAIN_GRACE_MS` constant)
- [ ] Regression test: a fixture endpoint that delays its response past the point the overlay's "Done Capturing" is clicked, confirming (a) a response that finishes within the grace period is now captured, and (b) one that doesn't still lets shutdown proceed (bounded, not hung). Closest existing analog: `tests/popup_race.spec.mjs`'s delayed-CDP-attach pattern.
- [ ] Burn down the 12 `status: todo` mutation-testing.kb entries filed 2026-07-22 for this fix (inject each, harden a test, flip to `done`/`gap` per the usual `docs/dev/mutation-testing.kb/` convention). Fixes 1–2: `pending-request-not-tracked.md`, `pending-request-not-resolved-on-finished.md`, `pending-request-not-resolved-on-failed.md`, `pending-request-redirect-reentrancy-guard-dropped.md`, `request-will-be-sent-passthrough-dropped.md`, `drain-grace-period-removed.md`, `drain-grace-period-race-changed-to-all.md`, `drain-grace-period-zeroed.md`. Fix 3: `drain-expiry-flush-removed.md`, `drain-expiry-flush-marker-dropped.md`, `truncation-marker-set-unconditionally.md`, `drain-expiry-flush-after-end.md`.
- [ ] Implement fix 3 (flush stashed RRs with truncation marker at grace expiry)
- [ ] Validate the fix by its own signature, not the original symptom: a post-fix live capture should contain responses (or truncation-marked RRs) for requests like the 2 `api/directory/servers` drops in the a59dc891 capture. The original zero-conversation-events symptom will NOT be resolved by this fix — that's `2026-07-22-001-*` (IndexedDB cache hydration).
- [ ] Run the Current Situation discriminator against existing `has_more=false` captures (rWBS-without-RR vs no-rWBS) and re-attribute the incubator's bullet in `docs/dev/design-incubators/chatfs-cli-mockup/.claude/todo.md` to this todo or to `2026-07-22-001-*` accordingly.

## Open Questions

- `DRAIN_GRACE_MS` value — 2000ms was a guess. Should it be configurable (CLI flag / `startCapture` option) rather than a constant? Note the floor is paid on *every* capture once fix 1 lands (open EventSource/long-poll connections never finish).
- Skip the grace period entirely on the window-close (cancel) path, or shorten it? The context is dying; no terminal events will arrive.
- Which of drain-race vs cache-hydration (`2026-07-22-001-*`) actually owns the `has_more=false` symptom? Decidable now from existing captures via the discriminator in Current Situation — doesn't need the fix to land first.

## Success Criteria

- [ ] A live capture where the human clicks "Done Capturing" shortly after content renders but before a slow request completes still captures that request's data (within the grace period).
- [ ] A capture with a genuinely hung request still terminates within a bounded time (no indefinite hang) — and the hung request's stashed headers appear in the output with the truncation marker, not silently absent.
- [ ] `tests/popup_race.spec.mjs` and all existing mutation-testing.kb-gated tests still pass unchanged.

## Notes

This file intentionally omits the full line-by-line diff sketch (available by re-deriving from the Proposed Solution) per the "broad strokes, not fine detail" instruction it was created under — the goal is letting a fresh agent rediscover the shape of the fix quickly, not pre-committing to exact code.
