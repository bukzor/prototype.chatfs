---
status: done
---

# `capture.mjs`: BARRIER `bindingCalled` emits without waiting for in-flight bodies

The core BARRIER invariant: every response the page claims to have
consumed by the time it calls `harBrowseMark("BARRIER:...")` must
appear in the event stream *before* the BARRIER. We enforce this by
holding the BARRIER emit until the snapshot of in-flight body-fetches
settles. If we emit immediately, RRs land after the BARRIER that
named them as consumed — downstream tools can't trust the BARRIER to
delimit work.

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
+        enqueue({ method: "Runtime.bindingCalled", params });
       } else {
         enqueue({ method: "Runtime.bindingCalled", params });
       }
```

## Test Coverage

`tests/barrier_smoke.spec.mjs`: "BARRIER: pending /payload responses
precede BARRIER in stream" — N=10 parallel /payload fetches with 20ms
delay, page fires `BARRIER:end` after `Promise.all`. Asserts every
/payload RR's stream index is `< barrierIdx`. With the mutation, the
BARRIER emits immediately when the binding event arrives — before
body-fetches have settled — so at least one RR lands after the BARRIER
and the test fails.
