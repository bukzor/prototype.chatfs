---
status: todo
---

# `capture.mjs`: event-iterator subscribes after CDP attach

`on(emitter, "event", ...)` must subscribe before any CDP event can
fire. Moving the subscription past `wireSession(page)` means events
emitted between `Network.enable` returning and the iterator existing
are lost. Manifests as missing early requests when capture starts on
a page that is already fetching at attach time.

## Injection

`src/capture.mjs`: move the `const queue = on(...)` line to *after*
the `await wireSession(page)` call.

## Status

Not yet attempted — deferred to a follow-up session. Hypothesis:
`har.spec.mjs` should catch it because the page's initial navigation
fires `Network.requestWillBeSent` for `/`, `/index.css`, `/index.js`
during `wireSession`, before the iterator subscribes. If subscription
happens after, those early RRs go to the EventEmitter with no
listener — node:events buffers them, but `on()` doesn't reach back.
Test should observe `byUrl(":port/")` returning undefined.
