---
managed-by: Skill(llm-subtask)
required-reading:
  - packages/har-browse/design.kb/030-requirements.kb/capture-cut-completeness.md
  - packages/har-browse/design.kb/040-design.kb/capture-cut-model.md
  - packages/har-browse/src/capture.mjs
suggested-reading:
  - packages/har-browse/.claude/todo.kb/2026-07-22-000-Done-Capturing-race-drops-in-flight-requests-with-no-drain.md
  - packages/har-browse/tests/inflight_drain.spec.mjs
cost-benefit-sweh:
  timebox:
    "@value": 2.0
    rationale: |
      Two CDP spikes runnable against the existing /hang fixture (no
      live capture needed), then a localized capture.mjs change that
      mostly *deletes* code (grace race, drainGraceMs plumbing) and
      rewrites 4 existing tests. Mutation re-file per
      Skill(mutation-testing) is the long pole.
    confidence: tentative
  benefit-2w:
    "@value": 1.0
    rationale: |
      Removes the 2s shutdown floor every capture currently pays
      (held-open EventSource connections are normal — a59dc891 holds
      one), and converts grace-expiry silent drops into explicit
      abort records, closing the last silent-loss path in the
      seen-then-dropped gap class. Also supersedes fix 3 of
      2026-07-22-000 at negative net code.
    confidence: confident
  cost-of-delay-2w:
    "@value": 0.3
    rationale: |
      Current grace drain is correct for completed-before-click
      payloads (the main chatfs workflow); the residual losses are
      bounded and now understood. Latency floor is annoying, not
      blocking.
    confidence: tentative
---

# Replace grace-period drain with abort-based cut at Done

**Priority:** Medium-High — deletes the last silent-loss path and a per-capture latency floor; mostly code removal.
**Complexity:** Low-Medium — two spikes gate the mechanism choice; the change itself is localized to `capture.mjs`'s drain.
**Context:** The 2026-07-22 grace-period drain (todo.kb `2026-07-22-000-*`, fixes 1+2) made the drain *wait* for in-flight requests, bounded by `drainGraceMs`. The 2026-07-23 cut-semantics analysis (see `design.kb/030-requirements.kb/capture-cut-completeness.md`) established that post-cut response data is outside the capture's cohort — so waiting for it buys nothing the requirement values, and the right move at the cut is to *force* termination, not to wait politely.

## Problem Statement

Three defects share the grace period as root cause:

1. **Every capture pays the full grace floor.** Held-open connections
   (EventSource, long-poll) never reach a terminal event, so the drain
   always runs out the clock — 2s of dead shutdown latency per capture
   (the a59dc891 capture's `mcp/v2/bootstrap` EventSource is the
   standing example).
2. **Grace expiry drops silently.** Requests still pending at expiry
   leave rWBS-without-RR with no terminal record — the same invisible-
   loss signature that caused the original 2026-07-22 misattribution,
   just narrower. Fix 3 (truncation-marker flush) was sketched to patch
   this with hand-rolled synthetic events; this todo supersedes it.
3. **The window-close path pays pure latency.** With the context dying,
   no terminal events can arrive; grace there is a guaranteed-useless
   wait (noted as an open question in `2026-07-22-000-*`, unresolved
   there, resolved here by detach-settlement).

## Proposed Solution

At cut detection, force every in-flight request to a real terminal
event, then wait — event-driven — for the pending ledger to settle:

1. **Cut:** per CDP session, disable networking. Primary candidate:
   `Network.emulateNetworkConditions {offline: true}` — expected (spike
   1) to abort in-flight requests with `loadingFailed
   (net::ERR_INTERNET_DISCONNECTED)` *and* fail-fast any post-cut
   requests. Fallback if in-flight requests survive offline emulation:
   `Page.stopLoading` + `Fetch.enable`-with-fail-all.
2. **Settle:** await the existing `pendingRequests`/`pendingInFlight`
   ledger (retained unchanged from fixes 1+2, including the redirect
   guard and the BARRIER-preserving two-set split). Abort events resolve
   it through the existing `onLoadingFailed` path — which already
   flushes stashed `awaitingBody` RRs bare. The browser's own
   `loadingFailed (canceled/aborted)` **is** the truncation record; no
   synthetic marker needed.
3. **Delivery barrier:** after settle, issue one throwaway command
   round-trip per session; when its response arrives, all events the
   browser emitted beforehand have been delivered (spike 2 verifies this
   ordering guarantee). Then `emit("end")`.
4. **Detach = settlement:** a CDP session that dies can never deliver
   terminal events — on session detach, settle that session's ledger
   entries. This makes the window-close path event-driven too and
   removes the last rationale for any timer.

Deletions: `DRAIN_GRACE_MS`, the `drainGraceMs` option threading, the
`Promise.race` in the drain. If a watchdog is kept at all (open
question), its firing is a logged defect, never a normal path.

## Implementation Steps

- [ ] **Spike 1 (gates mechanism):** against the existing `/hang` and
      `/abort-after-headers` fixtures, verify whether
      `Network.emulateNetworkConditions {offline: true}` aborts
      in-flight requests (both pre-`responseReceived` and mid-body) with
      a terminal `loadingFailed`. If not, measure `Page.stopLoading`
      coverage for fetch/XHR/EventSource. No live capture needed.
- [ ] **Spike 2 (gates barrier):** verify per-session ordering — a
      command response is delivered after all events the browser emitted
      before processing the command. If CDP doesn't guarantee this
      across the renderer/browser process boundary, design an
      alternative flush signal before relying on it.
- [ ] Implement the cut (per-session network disable at Done-detection
      and at context-close), ledger settle, delivery barrier, and
      detach-settles-ledger. Delete the grace machinery.
- [ ] Rewrite `tests/inflight_drain.spec.mjs`: the two grace-variant
      tests collapse (no constant left to protect); the hung-request
      test's assertion strengthens from "ends within grace + slack" to
      "ends promptly AND the hung request has an explicit terminal event
      in the output"; the prompt-end test keeps its three settle-path
      variants (finished/failed/redirect).
- [ ] Re-file mutation entries per `Skill(mutation-testing)` against the
      new design, then burn down. The four fix-3 prospective entries
      deleted 2026-07-23 (`drain-expiry-flush-removed`,
      `drain-expiry-flush-marker-dropped`, `drain-expiry-flush-after-end`,
      `truncation-marker-set-unconditionally`) carry these intents
      forward: (a) cut-abort call removed → hung request silent again;
      (b) truncated-vs-bodyless indistinguishable → assert the terminal
      event is present and canceled; (c) settle + barrier ordered before
      `emit("end")`; (d) no happy-path contamination (completed
      responses show no abort artifacts).
- [ ] Retire the grace-scoped `status: done` mutation entries
      (`drain-grace-period-removed.md`, `drain-grace-period-zeroed.md`)
      when their target code is deleted.
- [ ] Confirm `barrier_consumed.spec.mjs` unchanged-and-green (BARRIER's
      narrow `inFlight` snapshot is untouched by this redesign).

## Open Questions

- Does `emulateNetworkConditions {offline}` abort in-flight requests?
  (Spike 1. DevTools' offline toggle observably kills in-progress
  downloads and SSE, so expected yes — but per-session CDP behavior is
  unverified.)
- Keep a warn-only watchdog around the settle/barrier await, or trust
  detach-settlement fully? Leaning warn-only (stderr, reportable bug
  when it fires) — either way it must not gate correctness.
- Post-cut request events still pass through until `end` (honest record
  of the cut; zero filtering code). Confirm downstream consumers
  (chrome-har) tolerate trailing aborted entries — expected yes, aborted
  requests are ordinary HAR content.

## Success Criteria

- [ ] A capture holding a hung request and/or an open EventSource ends
      promptly after the cut (no 2s floor) with an explicit terminal
      event for every cohort request — the requirement doc's
      verification clause, exercised by test.
- [ ] No timer participates in drain correctness (no `setTimeout` in the
      drain path, or watchdog provably non-gating).
- [ ] Window close ends the stream promptly via detach-settlement.
- [ ] `pnpm test` green; BARRIER specs unchanged.

## Notes

Retained from the 2026-07-22 fixes 1+2 (still load-bearing, not
superseded): the `pendingRequests` ledger and `settlePending` call sites
(they become the settle-detector for the abort wave), the redirect
re-fire guard, and the `pendingInFlight`/`inFlight` two-set split
protecting BARRIER.

The streaming-bodies idea (`.claude/ideas.kb/2026-07-22-000-*`) is this
design's fidelity companion: without it, a request truncated at the cut
yields headers + abort record only; with
`Network.streamResourceContent`, the pre-cut delivered bytes are already
in the stream. Not required for the current revisit-capture workflow
(its payload completes before the human clicks Done).
