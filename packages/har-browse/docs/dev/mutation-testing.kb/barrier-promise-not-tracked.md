---
status: gap
attempts: 2
---

# `capture.mjs`: deferred BARRIER promise not added to `inFlight`

Concurrent BARRIERs are intended to serialize via the
allSettled-superset property: BARRIER B arriving while BARRIER A is
still deferring sees A's deferral-promise in its `[...inFlight]`
snapshot, so B's emit transitively waits for A's emit. Without the
outer `track(...)`, B's snapshot misses A's deferral promise — B can
emit before A even though A arrived first, and the on-wire ordering
of `BARRIER:` markers no longer matches arrival order.

## Injection

`src/capture.mjs`, in `onBindingCalled`:

```diff
       if (
         params.name === "harBrowseMark" &&
         params.payload?.startsWith?.("BARRIER:")
       ) {
-        track(
-          Promise.allSettled([...inFlight]).then(() =>
-            enqueue({ method: "Runtime.bindingCalled", params }),
-          ),
-        );
+        Promise.allSettled([...inFlight]).then(() =>
+          enqueue({ method: "Runtime.bindingCalled", params }),
+        );
       } else {
```

## Test Result

Attempt 1: existing `barrier_consumed.spec.mjs` (reentrant, 3 BARRIERs)
passes with the mutation injected. Hypothesis at the time: "test passes
by luck; mixed-delay adversarial timing would distinguish." Future work
recommended a `barrier_fifo.spec.mjs`.

Attempt 2 (this session): re-derived the invariant from first
principles and found the recommended test is **impossible**. The order
preservation is structural, not lucky.

### Proof

Let SA = `inFlight` snapshot taken at BARRIER A's arrival, SB at
BARRIER B's (A arrives before B). For each item `x` in SA:

- (a) `x` is still pending at B's arrival → `x ∈ SB` (inFlight only
  removes on settle via the `.finally(() => inFlight.delete(pr))` in
  `track()`), or
- (b) `x` settled in (A, B) → `settle(x) ≤ B-arrival`, and `x ∉ SB`.

`max(SA) = max settle-time over SA`. Every (b)-item has settle-time
≤ B-arrival; every (a)-item has settle-time ≥ B-arrival. So
`max(SA) = max settle-time over (a)-items` (taking max over the empty
set as -∞ when there are no (a)-items). Since (a)-items ⊆ SB,
`max(SB) ≥ max(SA)`. Therefore A's `Promise.allSettled([...SA])`
resolves no later than B's.

In the tail case `max(SB) = max(SA)`, both `allSettled` instances are
subscribed to the same final-settling promise — A's subscription
predates B's, so V8's per-promise microtask FIFO runs A's `.then(emitA)`
before B's `.then(emitB)`.

### Conclusion

The order-preservation invariant the `track(BARRIER promise)` is meant
to defend is delivered "for free" by inFlight's monotonic-removal
semantics. The `track` wrap is dead defense, in the same class as
`inject-overlay-not-awaited` (CDP serializes commands in receive order)
and `barrier-snapshot-not-frozen` (allSettled snapshots its iterable at
call time).

Confirmed empirically: 5 repeats × 2 BARRIER tests = 10 runs, all pass
with `track(...)` removed.

The `track(...)` wrap is worth keeping for *clarity* — it documents the
intent ("this BARRIER deferral is part of the in-flight set future
BARRIERs should wait on") and survives a future refactor that, say,
introduces a non-monotonic inFlight admission policy. But no test can
distinguish its presence from its absence under the current code.

## See Also

`inject-overlay-not-awaited` — CDP-serialization analog.
`barrier-snapshot-not-frozen` — same allSettled-snapshot family.
