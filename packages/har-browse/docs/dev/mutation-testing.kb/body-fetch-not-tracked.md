---
status: todo
---

# `capture.mjs`: body-fetch promise not added to inFlight

The `cdpHandlers["Network.loadingFinished"]` entry wraps the body-fetch
call in `track(...)`, which adds the promise to `inFlight` so BARRIER
snapshots include it. If the `track` wrap is dropped, the body-fetch
still runs but isn't tracked; BARRIER's `Promise.allSettled([...inFlight])`
snapshot can complete before the body lands, so the BARRIER emits with
the body's `Network.responseReceived` arriving AFTER it.

Distinct from `barrier-promise-not-tracked` (gap), which covers the
deferred-emit Promise for the BARRIER itself; this entry covers the
body-fetch Promise that the BARRIER waits on.

Hypothesis: `tests/barrier_consumed.spec.mjs` already catches this
(reentrant test asserts consumed RRs precede each BARRIER). Drive
through inject→test→revert to confirm and link the test.

## Injection

`src/capture.mjs`, `cdpHandlers`:
change `"Network.loadingFinished": (p) => track(onLoadingFinished(p)),`
to `"Network.loadingFinished": (p) => onLoadingFinished(p),`.
