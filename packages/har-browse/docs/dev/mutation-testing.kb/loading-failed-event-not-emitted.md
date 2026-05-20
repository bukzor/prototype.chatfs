---
status: done
---

# `capture.mjs`: `Network.loadingFailed` is not enqueued

`onLoadingFailed` emits two events: the stashed `Network.responseReceived`
(if one was captured) followed by `Network.loadingFailed` itself. If the
final enqueue is dropped, network failures vanish from the stream —
chrome-har sees no terminator for the request and HAR entries for failed
fetches lose their failure state (or are dropped entirely).

Distinct from `loading-failed-no-rr-flush` (gap), which covers the RR
flush; this one covers the LFail event itself.

## Injection

`src/capture.mjs`, `onLoadingFailed`:
delete the trailing `enqueue({ method: "Network.loadingFailed", params: lfail });`.

## Test Coverage

`tests/loading_failed.spec.mjs` — page fetches a closed local port
(`http://127.0.0.1:1/`), which triggers `Network.loadingFailed` from
the browser. The test asserts at least one `loadingFailed` event in
the captured stream. With the enqueue dropped, zero events match and
the assertion fails.
