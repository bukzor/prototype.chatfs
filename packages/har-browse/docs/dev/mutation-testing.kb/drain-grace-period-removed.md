---
status: todo
---

# `capture.mjs`: grace-period timeout removed from the final drain

**Priority:** High. **Confidence:** Medium.

Prospective — targets the fix in `packages/har-browse/.claude/todo.kb/
2026-07-22-000-Done-Capturing-race-drops-in-flight-requests-with-no-
drain.md`, not yet implemented. This is the safety net for the other
half of that fix (extended `inFlight` tracking, see
`pending-request-not-tracked.md`): once tracking starts at
`requestWillBeSent`, a request that never reaches a terminal CDP event
(genuinely hung, or the CDP session dies mid-flight) would block
`inFlight` forever. Since the caller only calls `context.close()` after
the events stream ends, that's a real deadlock — nothing left to abort
the hung request. If the bounded-timeout wrapper is removed (reverting
to bare `await Promise.allSettled([...inFlight])`), `har-browse` hangs
indefinitely on any such request, worse than today's behavior (silent
drop, but at least the process exits).

## Injection

```diff
   .finally(async () => {
-    await Promise.race([
-      Promise.allSettled([...inFlight]),
-      new Promise((resolve) => setTimeout(resolve, DRAIN_GRACE_MS)),
-    ]);
+    await Promise.allSettled([...inFlight]);
     emitter.emit("end");
   })
```

## Variant Injection

`race` → `all` fat-finger — a standard mutation operator, so a tool
would generate it independently — is observably identical, not the
milder always-waits-full-grace bug it first appears to be:
`Promise.all([A, B])` resolves only once *every* argument resolves, so
if `A` (`allSettled([...inFlight])`) never resolves, the timeout `B`
firing is irrelevant and the identical indefinite hang results.
(Folded from the former `drain-grace-period-race-changed-to-all.md`,
2026-07-22 — one test kills both; inject each variant in turn at
burn-down.)

```diff
-    await Promise.race([
+    await Promise.all([
       Promise.allSettled([...inFlight]),
       new Promise((resolve) => setTimeout(resolve, DRAIN_GRACE_MS)),
     ]);
```

## Anticipated Test Coverage

Needs a fixture request that never resolves (server accepts the
connection and never responds) plus a test-level guard timeout strictly
larger than `DRAIN_GRACE_MS` to prove the capture still ends — i.e., the
test itself must terminate in bounded time to prove the *absence* of a
hang, which is a slightly awkward shape (proving termination rather than
a value) but standard for liveness properties. Medium confidence in the
construction; whichever test lands must be verified against both
injection variants above.
