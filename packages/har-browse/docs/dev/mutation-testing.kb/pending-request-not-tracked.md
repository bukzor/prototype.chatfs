---
status: todo
---

# `capture.mjs`: new `requestWillBeSent` tracker not added to `inFlight`

**Priority:** High. **Confidence:** High.

Prospective — targets the fix sketched in `packages/har-browse/.claude/
todo.kb/2026-07-22-000-Done-Capturing-race-drops-in-flight-requests-with-
no-drain.md`, not yet implemented. This is the core mechanism of that
fix; if this mutation ships silently, the original bug (a request still
pending at "Done Capturing" time is dropped with zero trace) regresses
completely — the new tracking exists in name only.

If the new `Network.requestWillBeSent` handler creates the
resolve/promise pair but never calls `track(pr)`, the promise is never
added to `inFlight`. The drain's `Promise.allSettled([...inFlight])`
(or its grace-period-bounded successor) has nothing to wait on for that
request, so shutdown proceeds exactly as it does today — before a slow
response arrives.

## Injection

Once implemented, in the new `cdpHandlers["Network.requestWillBeSent"]`
handler:

```diff
   "Network.requestWillBeSent": (p) => {
     if (!pendingRequests.has(p.requestId)) {
       let resolve;
       const pr = new Promise((res) => { resolve = res; });
       pendingRequests.set(p.requestId, resolve);
-      track(pr);
     }
     enqueue({ method: "Network.requestWillBeSent", params: p });
   },
```

## Anticipated Test Coverage

A fixture request delayed past the point the overlay's "Done Capturing"
is clicked (analogous to `tests/popup_race.spec.mjs`'s delayed-CDP-attach
regime, but delaying the response itself rather than a popup's session
attach) should still appear in the captured stream once the fix lands.
With this mutation injected, that response goes missing again —
matching the exact live-capture symptom that motivated the fix.
