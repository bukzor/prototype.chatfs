# Devlog: 2026-07-23 — Capture cut semantics pivot; gap-closure planning

## Focus

Post-mortem discussion of the 2026-07-22 drain-race fix (`b571e99`)
escalated into a semantics question — what exactly is the capture
*obligated* to contain at "Done Capturing" time? — and from there into a
full plan for closing har-browse's remaining capture-completeness gaps.
This session produced docs and plans only; no code changed.

## What happened

- Evaluated `b571e99` (grace-period drain): correct against its own
  design, tests green, mutation-verified. But the design question
  "is the grace period a sleep-based race fix?" surfaced a sharper one:
  the grace period waits for *post-cut* response arrivals, and the user
  ruled those outside the capture's obligation.
- Established cut/cohort semantics and wrote them into the design.kb:
  the cohort is every network event that occurred before the Done cut;
  post-cut arrivals may be aborted. The causal argument: the human
  clicks Done after *seeing* the payload render, so witnessed data is
  always pre-cut. New requirement:
  `packages/har-browse/design.kb/030-requirements.kb/capture-cut-completeness.md`;
  new design entry (lanes model + gap taxonomy + drain history):
  `packages/har-browse/design.kb/040-design.kb/capture-cut-model.md`.
- Planned the drain redesign:
  `todo.kb/2026-07-23-000-Replace-grace-period-drain-with-abort-based-cut-at-Done.md`
  — force in-flight requests to real terminal events at the cut
  (offline emulation, spike-gated), await the existing pending ledger,
  per-session delivery barrier, session-detach-settles-ledger. No timer
  in the correctness path.
- Promoted the never-attached-targets idea to
  `todo.kb/2026-07-23-001-Zero-miss-target-coverage-via-Target-setAutoAttach.md`
  (venue spike first: Playwright transport vs raw CDP connection vs
  rust port).
- Widened `todo.kb/2026-07-22-001-*` (clearOriginStorage): cache_storage
  joins indexeddb in the default clear set; local_storage opt-in
  (auth-token risk); per-session `setCacheDisabled` +
  `setBypassServiceWorker`.

## Decisions

### Fix 3 (truncation-marker flush) superseded, not implemented

The grace-expiry flush and its synthetic `harBrowseTruncated` marker are
dead: aborting in-flight requests at the cut makes the browser's own
`loadingFailed` the truncation record, flowing through existing handler
paths. The four fix-3-scoped prospective mutation entries were deleted;
their intents are enumerated in `2026-07-23-000-*` for re-filing at
implementation. Retained from `b571e99` (load-bearing, not shotgun): the
`pendingRequests` ledger, redirect guard, and the
`pendingInFlight`/`inFlight` split protecting BARRIER.

### Timers are never synchronization

Codified in `capture-cut-model.md`: every wait must complete on an
observable event; when no event is guaranteed, force one (abort, treat
detach as settlement) rather than sleeping. Deadlines only as loud
watchdogs whose firing is a reportable defect.

## Next session

- Run the two spikes gating `2026-07-23-000-*` (offline-emulation abort
  behavior against `/hang`; CDP command/event ordering for the delivery
  barrier) — both runnable in the existing test harness, no live
  capture needed.
- `2026-07-22-001-*` (clearOriginStorage) remains the highest-value
  item and is implementable now; its live verification step is
  ask-first.
