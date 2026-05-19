---
status: done
---

# `capture.mjs`: event-iterator subscribes after CDP attach

`on(emitter, "event", ...)` must subscribe before any CDP attachment.
`Page.enable` / `Runtime.enable` replay existing state via events (e.g.
`Runtime.executionContextCreated` for the about:blank initial frame).
If the queue is subscribed after `wireSession()`, those replay events
fire to an emitter with no listener — `on()` does not retroactively
capture past emits — and are silently lost. Manifests as missing
initial execution contexts and missing frame events on the very first
page; subsequent navigations (after queue creation) flow normally.

## Injection

`src/capture.mjs`: move the `const queue = on(...)` line to *after*
the `await wireSession(page)` call.

## Test Coverage

`tests/attach_replay.spec.mjs` — collects events from `startCapture`
and asserts the stream contains at least one
`Runtime.executionContextCreated` with `context.origin === "://"`
(CDP's opaque-origin form for about:blank). Without the mutation, 4
contexts are captured (2 about:blank replays + 2 for the navigated
origin); with the mutation, both about:blank replays are dropped and
the assertion fails (received 0).
