---
managed-by: Skill(llm-subtask)
required-reading:
  - packages/har-browse/design.kb/030-requirements.kb/capture-cut-completeness.md
  - packages/har-browse/design.kb/040-design.kb/capture-cut-model.md
  - packages/har-browse/src/capture.mjs
suggested-reading:
  - packages/har-browse/tests/popup_race.spec.mjs
  - packages/har-browse/dev.kb/rust-port.md
  - packages/har-browse/design.kb/040-design.kb/capture-tap.kb/tap-point.md
  - packages/har-browse/design.kb/070-future-work.kb/capture-implementation-frontier.kb/pure-cdp-spawned.md
cost-benefit-sweh:
  timebox:
    "@value": 2.5
    rationale: |
      Forensic pass (0.5) + venue spike (0.5) are cheap and decisive.
      Implementation cost depends entirely on the venue verdict:
      auto-attach on a separate raw CDP connection is a contained
      change; retrofitting through Playwright's transport may prove
      impractical and punt implementation to the rust port.
    confidence: tentative
  benefit-2w:
    "@value": 0.5
    rationale: |
      No confirmed chatfs payload loss on non-page targets yet —
      absence of evidence is structural (invisible traffic leaves no
      trace), which is itself the argument for the forensic pass.
      Closes the requested-but-never-seen gap class and makes the
      never-requested class forensically distinguishable from it.
    confidence: tentative
  cost-of-delay-2w:
    "@value": 0.2
    rationale: |
      Risk is provider-behavior-shaped (a provider moving payload
      behind a service worker), not time-shaped. Low until evidence
      appears; the forensic pass is the cheap early-warning.
    confidence: tentative
---

# Zero-miss target coverage via Target.setAutoAttach

**Priority:** Medium — structural coverage gap, no confirmed victim yet; the cheap forensic step prices the rest.
**Complexity:** Medium — the CDP mechanism is well understood; the risk is transport integration under Playwright.
**Context:** Promoted 2026-07-23 from `ideas.kb/2026-07-22-001-capture-requests-on-targets-we-never-attach.md` (identified as gap "D4" in the 2026-07-22 request-lifetime analysis). The idea deferred implementation to the rust port; the 2026-07-23 capture-gap planning committed to the *mechanism* now, with the venue (Node vs rust port) as the first decision point. This is the "requested, never seen" class in `design.kb/040-design.kb/capture-cut-model.md`, and this todo is the implementation for requirement 1 ("coverage spans the whole session") of `design.kb/030-requirements.kb/capture-cut-completeness.md`.

## Problem Statement

Per-page CDP sessions (`context.newCDPSession` wired via
`context.on("page")` in `capture.mjs`) miss two classes of traffic that
client JS can see:

1. **Pre-attach window** — requests a popup fires between page creation
   and its `Network.enable` ack. `tests/popup_race.spec.mjs` proves the
   attachment is awaited, but nothing covers events *before* enable; CDP
   does not replay.
2. **Non-page targets** — service workers, shared workers, OOPIFs, and
   prerender targets have their own CDP targets; per-page sessions
   receive zero of their Network events. Service-worker-served fetches
   (the cache-first pattern chat apps favor) are invisible today.

Both classes leave no rWBS — forensically indistinguishable from
persisted-cache hydration (`2026-07-22-001-*`) in a per-page capture,
which corrupts root-cause analysis even when no payload is lost.

## Proposed Solution

One mechanism closes both: a browser-target session issuing
`Target.setAutoAttach {autoAttach: true, waitForDebuggerOnStart: true,
flatten: true}`. Each new target pauses at creation until we enable
Network (and apply per-session capture settings), then
`Runtime.runIfWaitingForDebugger` releases it. Zero-miss by
construction — the target cannot run before instrumentation is in
place — replacing the reactive `context.on("page")` wiring.

Interim mitigation, independent of venue:
`Network.setBypassServiceWorker(true)` on existing per-page sessions
routes fetches network-direct, converting most service-worker traffic
into ordinary page-session events without touching the profile. (Owned
by `2026-07-22-001-*`'s session-settings step; noted here because it
shrinks this todo's urgency.)

## Implementation Steps

- [ ] **Forensic pass (decides urgency):** check existing captures per
      provider for service-worker registration and fetch-event handlers;
      one `navigator.serviceWorker.getRegistrations()` evaluate per live
      provider page. A registered SW plus payload gaps is the tell.
- [ ] **Venue spike (decides architecture):** determine whether
      Playwright's transport can carry our own auto-attach — does its
      `CDPSession` surface `sessionId`-tagged messages for child
      sessions we create, and do two clients using
      `waitForDebuggerOnStart` (Playwright's own attach machinery plus
      ours) coexist? Candidate outcomes:
      1. Separate raw CDP connection for capture (`--remote-debugging-
         port`), Playwright only drives UI — cleanest, biggest refactor.
      2. Auto-attach through Playwright's session — smallest diff if the
         transport permits it.
      3. Neither is practical under Node → implement in the rust port
         (chromiumoxide makes auto-attach the natural shape); spec the
         invariant into the rust-port charter now.
- [ ] Implement per venue verdict: on attach of any target, apply the
      standard session setup (Network.enable + capture settings) before
      release; route all sessions' events into the shared queue;
      per-session `awaitingBody`/ledger as today.
- [ ] Fixtures + tests: SW-registering page (cache-first fetch handler),
      popup firing a request at parse time (pre-attach window),
      cross-origin iframe (second listener in `tests/_common/server.mjs`).
      Mutation entries per `Skill(mutation-testing)` at implementation.
- [ ] Verify the passive-observation stance: auto-attach +
      `waitForDebuggerOnStart` must not observably perturb page behavior
      (timing shifts are acceptable; functional changes are not).

## Open Questions

- Does any chatfs provider actually serve payload through a service
  worker? (Forensic pass answers; decides now-vs-port.)
- Do dedicated workers report Network events through the parent page's
  session in current Chrome (post network-service consolidation), or do
  they need their own attach? Affects fixture coverage matrix.
- Interaction with the abort-based cut (`2026-07-23-000-*`): the cut
  must reach *every* attached session, including worker/SW sessions —
  auto-attach naturally provides the session enumeration the cut needs.

## Success Criteria

- [ ] A popup's parse-time request appears in the capture (rWBS + RR) —
      strictly stronger than `popup_race.spec.mjs`'s current guarantee.
- [ ] A fetch served by a service worker's cache-first handler appears
      in the capture, attributable to its target.
- [ ] A cross-origin iframe's subresource request appears in the capture.
- [ ] Existing suites green; no functional perturbation of fixture pages.

## Notes

Idea-stage analysis (2026-07-22) noted the rust-port charter as the
natural venue and `dev.kb/rust-port.kb/commits.kb/1050-causal-watermark.md`
as related body-integrity context. If the venue verdict is (3), this
file's invariants and fixtures transfer to the charter rather than being
re-derived.
