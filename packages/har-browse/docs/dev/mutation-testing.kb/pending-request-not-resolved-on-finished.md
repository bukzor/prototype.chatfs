---
status: todo
---

# `capture.mjs`: `settlePending` not called from `onLoadingFinished`

**Priority:** Medium. **Confidence:** Medium.

Prospective — targets the fix in `packages/har-browse/.claude/todo.kb/
2026-07-22-000-Done-Capturing-race-drops-in-flight-requests-with-no-
drain.md`, not yet implemented.

If `onLoadingFinished` enqueues the response as today but never calls
`settlePending(lf.requestId)`, the per-request promise added at
`Network.requestWillBeSent` time (see `pending-request-not-tracked.md`)
never resolves. The response data itself still lands in the stream —
`onLoadingFinished`'s existing enqueue logic doesn't depend on
`settlePending` — so this is *not* a data-loss regression. It's a
shutdown-latency regression: that tracker sits in `inFlight` forever,
forcing every capture to wait out the full grace-period timeout (see
`drain-grace-period-removed.md`) before ending, even when every request
actually finished promptly.

## Injection

```diff
 async function onLoadingFinished(lf) {
   const rr = awaitingBody.get(lf.requestId);
   awaitingBody.delete(lf.requestId);
   if (rr) { ... enqueue({ method: "Network.responseReceived", params: rr }); }
   enqueue({ method: "Network.loadingFinished", params: lf });
-  settlePending(lf.requestId);
 }
```

## Anticipated Test Coverage

Needs a timing-sensitive assertion: a capture where all requests finish
quickly should end shortly after "Done Capturing" is clicked, not after
the full `DRAIN_GRACE_MS`. Confidence is Medium rather than High because
timing-based assertions are more prone to flakiness than the equality
-style checks used elsewhere in this kb — may end up needing a generous
margin or could plausibly land as `gap` if hardening proves impractical
(compare the reasoning in `done-finally-skips-inflight-drain.md`'s "See
Also" section, which had similar difficulty constructing a reliable
slow-async-step regime).

Robustness technique (2026-07-22): make `DRAIN_GRACE_MS` injectable via
`startCapture` and set it *huge* in this test (e.g. 60s), then assert
the capture ends well under it (e.g. <5s) after all requests finish.
That converts a tight wall-clock margin into a wide liveness bound —
the mutant forces a 60s wait, the correct code ends in milliseconds, and
the 12x gap absorbs any CI jitter.
