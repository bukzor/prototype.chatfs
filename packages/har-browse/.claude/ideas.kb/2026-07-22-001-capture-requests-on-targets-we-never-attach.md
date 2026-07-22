---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    "@value": 0.5
    rationale: |
      Exploration only: confirm which chatfs-relevant traffic (if any)
      rides on non-page targets, and spec the invariant for the rust
      port. Implementing under Playwright is deliberately out of scope —
      it fights Playwright's own attach machinery.
  benefit-2w:
    "@value": 0.5
    rationale: |
      No confirmed chatfs payload loss yet — service-worker-served or
      pre-attach traffic is invisible, so absence of evidence is
      structural. Cheap insurance: one forensic pass decides whether
      this matters now or only for the port.
---

# har-browse: capture requests on targets we never attach

## The Idea

Per-page CDP sessions miss two classes of traffic that client JS can
see:

1. **Pre-attach window** — requests a popup fires between page creation
   and its `Network.enable` ack. `tests/popup_race.spec.mjs` proves the
   attachment is awaited, but nothing covers events *before* enable.
2. **Non-page targets** — service workers, shared/dedicated workers,
   OOPIFs have their own CDP targets; per-page sessions receive zero of
   their Network events. Service-worker-served fetches (the cache-first
   pattern chat apps favor) are invisible today.

Known fix shape: a browser-target session with `Target.setAutoAttach
{flatten, waitForDebuggerOnStart}` — new targets pause at creation
until Network is enabled, then `Runtime.runIfWaitingForDebugger`.
Zero-miss attach, replacing the reactive `context.on("page")` wiring.

Identified 2026-07-22 as gap "D4" in the request-lifetime analysis that
produced the drain-race and IndexedDB-hydration todos. Deferred to the
rust port: retrofitting auto-attach under Playwright fights its own
attach machinery, whereas under chromiumoxide it's the natural shape.

## Potential Benefits

- Closes the last structural coverage gap in "every response client JS
  could have seen" — the drain/flush work covers lifecycle, this covers
  topology.
- Defines "complete capture" for the rust port before its CDP layer is
  designed, instead of retrofitting after.

## Open Questions / Unknowns

- Does any chatfs provider actually serve payload through a service
  worker? (Forensic: check existing captures for SW registration and
  fetch-event handlers; a capture with a registered SW and payload
  gaps is the tell.)
- Does `Target.setAutoAttach` + `waitForDebuggerOnStart` perturb page
  behavior enough to violate the passive-observation stance?

## Exploration Notes

Distinct from the drain race (lifecycle: seen-but-dropped) and
IndexedDB hydration (never-requested): this class is
requested-but-never-seen — no rWBS at all, on a target we hold no
session for. Forensically indistinguishable from hydration in a
per-page capture, which is another reason to close it eventually.

## Next Steps (if pursuing)

- [ ] Forensic pass over existing captures for service-worker payload
      serving (decides now-vs-port urgency)
- [ ] Spec the auto-attach invariant into the rust-port charter
      (~0850, per the 2026-07-22 analysis) / eventual
      barrier-invariants doc

## Lifecycle

**Status:** Exploring — expected to promote into the rust-port charter
rather than Node-side work.
