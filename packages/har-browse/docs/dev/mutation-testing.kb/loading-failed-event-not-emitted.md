---
status: todo
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

## Fixture needed

`toy_server/` route that fails the request — e.g., terminate the
connection mid-headers, or simply trigger a `fetch("http://127.0.0.1:1")`
to a closed port from the page. Test asserts that the captured events
include a `Network.loadingFailed` for that request.
