---
status: todo
---

# `capture.mjs`: new `requestWillBeSent` handler drops the raw passthrough enqueue

**Priority:** Medium-High. **Confidence:** High.

Prospective — targets the fix in `packages/har-browse/.claude/todo.kb/
2026-07-22-000-Done-Capturing-race-drops-in-flight-requests-with-no-
drain.md`, not yet implemented.

`Network.requestWillBeSent` isn't special-cased in `cdpHandlers` today —
it flows through the generic passthrough branch (`(p) => enqueue({
method: name, params: p })`), same as every other unhandled CDP method.
The planned fix adds a dedicated handler (to attach tracking) that must
preserve this raw passthrough. If the new handler tracks the request but
forgets to re-enqueue the event itself, `Network.requestWillBeSent`
silently vanishes from the output stream entirely for every request —
independent of the race-condition fix, and worse in one sense: today's
bug loses data intermittently (timing-dependent); this regression would
lose an entire event type unconditionally, every capture, every request.

## Injection

```diff
   "Network.requestWillBeSent": (p) => {
     if (!pendingRequests.has(p.requestId)) {
       let resolve;
       const pr = new Promise((res) => { resolve = res; });
       pendingRequests.set(p.requestId, resolve);
       track(pr);
     }
-    enqueue({ method: "Network.requestWillBeSent", params: p });
   },
```

## Anticipated Test Coverage

Straightforward equality-style check, no timing involved: capture any
page load and assert at least one `Network.requestWillBeSent` event
appears in the output stream. High confidence — this is the same class
of check `tests/har.spec.mjs` / `barrier_smoke.spec.mjs` already do for
other event types.
