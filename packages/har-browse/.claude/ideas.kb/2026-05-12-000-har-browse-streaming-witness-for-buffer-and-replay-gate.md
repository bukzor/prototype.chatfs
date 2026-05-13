---
anthropic-skill-ownership: llm-subtask
cost-benefit-sweh:
  timebox:
    @value: 1.0  # SWE-hours
    rationale: |
      One focused session to: rework the test fixture for concurrent
      iteration on `session.events`, add the BARRIER-arrival deadline
      assertion, optionally add body.t timestamps for diagnostic skew.
  benefit-2w:
    @value: 0.5
    rationale: |
      Low immediate payoff: current capture.mjs is streaming, so the
      gate would catch a regression that hasn't happened. Value rises
      sharply when the trigger conditions hit (see below).
---

# har-browse: streaming witness for buffer-and-replay gate

## The Idea

`barrier_consumed.spec.mjs` covers most evil twins but doesn't gate
"buffer-and-replay" — an implementation that internally buffers every
CDP event and emits them sorted at end-of-capture passes every existing
assertion. Streaming is currently load-bearing for the real-world
contract (live HAR viewer, mid-capture progress feedback, etc.) but
unverified.

Close the gap by adding a streaming witness: have the test iterate
`session.events` concurrently with page activity and assert that BARRIER
arrives at the test iterator before `page.click("#capture-done")`
resolves. Buffer-and-replay forces BARRIER's arrival until after
`done.finally`, well after the click.

## Potential Benefits

- Closes the last *plausible-naive* evil twin in the suite (buffer-and-
  replay is the simplest alternative implementation that satisfies
  every existing assertion).
- Raises "passing the suite implies a desirable implementation"
  confidence from ~75% to ~85–90%.
- Constrains future refactors of capture.mjs to preserve streaming —
  acts as a guardrail against accidental drift to buffered semantics.

## Open Questions / Unknowns

- Exact deadline slack for the BARRIER-before-click assertion. Page
  click takes some wall-clock time (Playwright actionability waits +
  dispatch). Need to calibrate so the assertion fires on real buffering
  but not on jitter under load.
- Whether body-side `t` timestamps (page-emitted `performance.now()`)
  give enough additional signal to justify the wire-format change, or
  whether the deadline-only check is sufficient. Probably skip
  timestamps for the first pass; add only if the deadline check proves
  flaky or insufficient.
- Does the same witness extend to the reentrant flavor? Each BARRIER
  has its own deadline — moderate complexity bump.

## Exploration Notes

Sketch of the structural change to `barrier_consumed.spec.mjs`:

```js
let barrierArrivalWall = null;
const drain = (async () => {
  for await (const msg of session.events) {
    if (isBarrier(msg) && barrierArrivalWall === null) {
      barrierArrivalWall = Date.now();
    }
    messages.push(msg);
  }
})();

await session.page.evaluate(/* ... harBrowseMark fires here ... */);
const clickStart = Date.now();
await session.page.click("#capture-done");
expect(
  barrierArrivalWall,
  "BARRIER arrived at iterator before click resolves",
).toBeLessThan(clickStart + SLACK_MS);
await drain;
```

Key insight: buffer-and-replay can fake any *internal* timestamp
relationship (preserves CDP timestamps, can sort by them). What it
can't fake is the relationship between message arrival and the test's
own wall clock — concurrent iteration is the only way to surface that.

Related: existing test consumes messages post-hoc into an array. Move
collection into the concurrent drain so the wall-clock observation is
possible.

## Trigger Conditions

Promote from "idea" to `todo.kb/` when any of these fires:

- Major rewrite of `capture.mjs` is planned (the gate constrains the
  rewrite to stay streaming during refactor turbulence).
- A second consumer of `session.events` is added that depends on
  streaming (live HAR viewer, progress UI, anything user-visible
  during capture). At that point streaming is observable contract, not
  aesthetic.
- A real bug is suspected in streaming behavior (e.g., events appear
  delayed in some downstream tool).

## Next Steps (if pursuing)

- [ ] Calibrate `SLACK_MS` against current implementation across N runs.
- [ ] Add concurrent iteration to `barrier_consumed.spec.mjs`
      (adversarial flavor first; consider reentrant flavor extension).
- [ ] Confirm assertion fires when a deliberate buffer-and-replay
      stub is swapped in (bug induction round, like the earlier
      evil-twin proof).

## Lifecycle

**Status:** Exploring
