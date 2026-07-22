---
status: done
---

# `capture.mjs`: `settlePending` not called from `onLoadingFailed`

**Priority:** Medium. **Confidence:** Medium.

Prospective — targets the fix in `packages/har-browse/.claude/todo.kb/
2026-07-22-000-Done-Capturing-race-drops-in-flight-requests-with-no-
drain.md`, landed 2026-07-22 in `capture.mjs`. Same defect as
`pending-request-not-resolved-on-finished.md`, on the failure path: if
`onLoadingFailed` enqueues `Network.loadingFailed` as today but never
calls `settlePending(lfail.requestId)`, a failed request's tracker never
resolves — shutdown-latency regression (full grace-period wait), not
data loss, since the existing enqueue logic is unaffected.

## Injection

```diff
 function onLoadingFailed(lfail) {
   const rr = awaitingBody.get(lfail.requestId);
   awaitingBody.delete(lfail.requestId);
   if (rr) enqueue({ method: "Network.responseReceived", params: rr });
   enqueue({ method: "Network.loadingFailed", params: lfail });
-  settlePending(lfail.requestId);
 }
```

## Test Coverage

Confirmed 2026-07-22: `tests/inflight_drain.spec.mjs` "capture ends promptly once in-flight requests settle, not after the full grace period" -- injected, observed red, reverted, observed green.

Same shape as `pending-request-not-resolved-on-finished.md` but needs a
fixture request that *fails* (aborted/refused) rather than one that
completes — e.g. a toy-server route that resets the connection.
Confidence: Medium, same flakiness caveat as the `loadingFinished`
sibling entry — and the same robustness technique applies (injectable
`DRAIN_GRACE_MS` set huge, assert prompt end; see that entry).
