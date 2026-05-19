---
status: gap
attempts: 1
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

Existing `barrier_consumed.spec.mjs` (reentrant) passes with the
mutation injected. The serialization invariant the `track(...)` is
defending — "concurrent BARRIERs serialize via allSettled's superset
ordering" — only manifests when an *earlier* BARRIER's snapshot waits
longer than a *later* BARRIER's snapshot. In the existing fixture all
`/payload` body-fetches are roughly equal in duration (no artificial
per-id delays), so microtask scheduling happens to preserve FIFO order
without `track(...)`. The test passes by luck.

To catch this reliably we'd need adversarial-delay timing:
slow-fetching requests in BARRIER#1's snapshot, fast-fetching in
BARRIER#2's. Toy server supports `?delay=N` already. Future work:
add `tests/barrier_fifo.spec.mjs` with mixed delays so BARRIER#2's
snapshot resolves before BARRIER#1's, and assert the captured
BARRIER stream order matches arrival order (via the
threshold-vs-consumed-size check that's already in the reentrant
test — which fails as long as `findBarriers` iterates in stream
order).
