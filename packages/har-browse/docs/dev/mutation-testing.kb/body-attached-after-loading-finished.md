---
status: gap
attempts: 1
---

# `capture.mjs`: `loadingFinished` emitted before `responseReceived`

The wire format `chrome-har` consumes assumes RR precedes LF per
request — RR carries the response, LF carries the size/timing close.
Swapping the order can cause `chrome-har` to either drop the response
entry or stitch headers/body onto the wrong request.

## Injection

`src/capture.mjs`, in `onLoadingFinished`:

```diff
-        enqueue({ method: "Network.responseReceived", params: rr });
-      }
-      enqueue({ method: "Network.loadingFinished", params: lf });
+      }
+      enqueue({ method: "Network.loadingFinished", params: lf });
+      if (rr) enqueue({ method: "Network.responseReceived", params: rr });
```

## Test Result

`tests/har.spec.mjs` passes with the order swapped. `chrome-har`
joins RR + LF by `requestId` and doesn't require strict CDP order; it
tolerates LF arriving first. None of the message-iterating tests
(barrier_smoke, barrier_consumed) assert RR-before-LF either — they
filter by method type, not by relative position.

To catch this, would need to assert per-request that the RR JSONL
index is `< LF`'s. Plausible but unmotivated: the original premise
("chrome-har may drop response entry") didn't survive contact with
chrome-har's actual behavior. Recording as gap; the bare-eye severity
of the mutation is lower than initially planned.
