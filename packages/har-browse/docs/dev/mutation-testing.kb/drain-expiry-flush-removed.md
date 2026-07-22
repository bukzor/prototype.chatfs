---
status: todo
---

# `capture.mjs`: grace-expiry flush of stashed `awaitingBody` entries removed

**Priority:** High. **Confidence:** High.

Prospective — targets fix 3 in `packages/har-browse/.claude/todo.kb/
2026-07-22-000-Done-Capturing-race-drops-in-flight-requests-with-no-
drain.md`, not yet implemented. Fix 3's contract: when the grace period
expires with requests still outstanding, their stashed
`Network.responseReceived` params (headers arrived, body never finished)
are emitted with a truncation marker instead of being discarded. If the
flush is deleted, a hung-after-headers request once again leaves zero
trace beyond its `requestWillBeSent` — restoring exactly the
invisible-loss property that let the 2026-07-22 zero-conversation-events
symptom be misattributed to this bug in the first place (see that todo's
Current Situation).

## Injection

Once implemented (schematic — the flush presumably iterates per-session
`awaitingBody` maps via callbacks registered at `attachCapture` scope):

```diff
   .finally(async () => {
     await Promise.race([
       Promise.allSettled([...inFlight]),
       new Promise((resolve) => setTimeout(resolve, DRAIN_GRACE_MS)),
     ]);
-    for (const flush of flushers) flush();
     emitter.emit("end");
   })
```

## Anticipated Test Coverage

Fixture endpoint that sends response headers then holds the body open
past a small test-configured grace period; click Done; drain. Assert the
output contains a `Network.responseReceived` for that URL with
`response.harBrowseTruncated === true` and no `response.body`. Equality-
style presence check, no tight timing — the request is *guaranteed*
unfinished at expiry because the server never finishes it.
