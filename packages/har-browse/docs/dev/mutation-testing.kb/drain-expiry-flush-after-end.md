---
status: todo
---

# `capture.mjs`: grace-expiry flush enqueued after `emitter.emit("end")`

**Priority:** Medium. **Confidence:** High.

Prospective — targets fix 3 in `packages/har-browse/.claude/todo.kb/
2026-07-22-000-Done-Capturing-race-drops-in-flight-requests-with-no-
drain.md`, not yet implemented. The events iterator is
`on(emitter, "event", { close: ["end"] })` — anything enqueued after
`"end"` fires never reaches the consumer. If the flush runs after the
end-emit (a two-line ordering swap), fix 3 executes completely — marker
set, RRs enqueued — and every flushed event lands in a closed queue.
Behaviorally identical to `drain-expiry-flush-removed.md`, but nastier
to debug: the flush code visibly runs under a debugger, and the loss is
only observable at the consumer.

## Injection

```diff
   .finally(async () => {
     await Promise.race([
       Promise.allSettled([...inFlight]),
       new Promise((resolve) => setTimeout(resolve, DRAIN_GRACE_MS)),
     ]);
-    for (const flush of flushers) flush();
     emitter.emit("end");
+    for (const flush of flushers) flush();
   })
```

## Anticipated Test Coverage

Killed by the same consumer-side assertion as
`drain-expiry-flush-removed.md` — the truncated RR must appear *in the
drained output*, which is exactly what post-end enqueueing prevents.
This is why that assertion must drain `session.events` to completion
rather than inspecting any internal state: the mutation is invisible
anywhere upstream of the iterator.
