---
status: gap
attempts: 1
---

# `capture.mjs`: stale RR entries linger in `awaitingBody`

`awaitingBody.delete(lf.requestId)` clears the stash after an LF/LFail
is handled. Without the delete, the Map grows monotonically through
the session. The leak is invisible on short captures but unbounded on
long ones; also defangs the (theoretical) guard against requestId
reuse — a second RR for the same id would see the prior RR's body
stash instead of its own.

## Injection

`src/capture.mjs`, in both `onLoadingFinished` and `onLoadingFailed`:

```diff
       const rr = awaitingBody.get(lf.requestId);
-      awaitingBody.delete(lf.requestId);
```

Likely **gap** unless we add memory-pressure / Map-size assertions.

## Test Result

All 8 Playwright tests pass with the delete dropped. The Map leak is
not behaviorally observable in short captures; no test exposes
`awaitingBody.size` or otherwise inspects the internal state. To
catch this, expose a `__captureDebugState()` hook or assert
`process.memoryUsage()` deltas across many captures — neither is
warranted for a single-line guard. Mutation kept as recorded
intent.
