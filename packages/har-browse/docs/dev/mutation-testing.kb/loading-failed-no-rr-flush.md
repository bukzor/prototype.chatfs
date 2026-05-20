---
status: done
---

# `capture.mjs`: `onLoadingFailed` doesn't flush the stashed RR

When a request that already received headers fails (e.g. mid-body
TCP reset), there's a stashed RR with no body. Current code emits
that bare RR before the LFail so chrome-har sees a response entry.
Drop the flush and the failure shows up in HAR with no response
metadata at all — chrome-har may also miscount totals.

## Injection

`src/capture.mjs`, in `onLoadingFailed`:

```diff
       const rr = awaitingBody.get(lfail.requestId);
       awaitingBody.delete(lfail.requestId);
-      if (rr) enqueue({ method: "Network.responseReceived", params: rr });
       enqueue({ method: "Network.loadingFailed", params: lfail });
```

## Test Coverage

`tests/loading_failed.spec.mjs` — "RR flushed for mid-body abort
(responseReceived precedes loadingFailed)". The `tests/_common/server.mjs`
`/abort-after-headers` route calls `res.flushHeaders()` then
`socket.destroy()` after a 10ms delay so the browser receives headers
(emits `responseReceived`) before the RST (emits `loadingFailed`).
The test asserts the stashed RR is flushed by `onLoadingFailed` —
without the flush, `rrIdx` is `-1` and the test fails.
