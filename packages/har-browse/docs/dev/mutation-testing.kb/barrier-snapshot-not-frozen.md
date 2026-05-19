---
status: gap
attempts: 1
---

# `capture.mjs`: BARRIER waits on the live `inFlight` Set, not a snapshot

`Promise.allSettled([...inFlight])` freezes the membership at the
moment the BARRIER arrives. Pass the live Set and Promise.allSettled
still gets an iterable — it just snapshots itself — so this mutation
manifests on multi-page captures where `wireSession(p)` adds new
in-flight tracker promises mid-defer. Per-BARRIER semantics drift:
a BARRIER that should have closed at body-fetch N+5 now waits on
body-fetches that arrived *after* the page said it was done.

## Injection

`src/capture.mjs`, in `onBindingCalled`:

```diff
-        track(
-          Promise.allSettled([...inFlight]).then(() =>
+        track(
+          Promise.allSettled(inFlight).then(() =>
             enqueue({ method: "Runtime.bindingCalled", params }),
           ),
         );
```

Subtle — may be **gap** without a multi-page race fixture.

## Test Result

The mutation is *not actually a bug*. `Promise.allSettled(iterable)`
iterates its argument synchronously at call time and snapshots the
list of promises right there — whether the argument is a Set ref or a
fresh array makes no observable difference. Later additions to the
Set after the `Promise.allSettled(...)` line has executed don't reach
the allSettled internals.

So the "live ref" version is semantically identical to the spread
version. The spread `[...inFlight]` in the original is *stylistically*
clearer ("this is a snapshot") but doesn't add anything the runtime
wasn't already going to do.

Recording as `gap` because the original "this is testable" premise was
wrong. No realistic test can distinguish the two forms, because there
is no behavioral difference to distinguish.
