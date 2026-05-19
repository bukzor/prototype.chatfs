---
status: gap
attempts: 1
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

## Test Result

All 8 Playwright tests pass with the flush dropped. No existing
fixture serves a request that succeeds headers then fails mid-body —
neither the toy_server nor example.com produces a stashed-RR-+-LFail
condition. To catch this, the toy server needs a route that writes
headers then aborts the connection mid-body (`socket.destroy()` after
`res.flushHeaders()`).
