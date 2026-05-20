---
status: done
---

# `capture.mjs`: track() wrapper removed from page-listener wireSession

`context.on("page", (p) => track(wireSession(p)))` — `track()` adds
the wiring promise to `inFlight`, so the close()-time
`Promise.allSettled([...inFlight])` waits for popup CDP attachment
before emitting `end`. Drop the track wrapper and a popup opening
just before Done can have its `wireSession` cancelled mid-setup; its
early events vanish. Distinct from `context-on-page-listener-removed`
which removes the listener entirely.

## Injection

`src/capture.mjs`:

```diff
-  context.on("page", (p) => track(wireSession(p)));
+  context.on("page", (p) => wireSession(p));
```

## Test Coverage

`tests/popup_race.spec.mjs` — "popup wireSession is awaited at close
(slow CDP attach)" — monkey-patches the popup wireSession's
`session.send("Runtime.enable")` to sleep 500ms, opens a popup whose
`/payload?delay=300` body arrives AFTER the Done click, and asserts
the popup RR reaches the iterator.

With `track()`, the page-listener adds the popup's wireSession to
`inFlight`; close()'s `Promise.allSettled([...inFlight])` waits the
full 500ms for wireSession to finish, during which the popup's
loadingFinished arrives and the body-fetch (also tracked) lands its
RR in the queue. Without `track()`, allSettled completes near-instantly
post-click; emit('end') fires before the popup's events arrive, so the
RR is dropped on the floor.

Verified: 10/10 pass with `track()`; 5/5 fail without it.

Design note: setting the delay AFTER `Network.enable` acks is critical
— if the delay were on `newCDPSession` itself, Chromium would never
deliver popup Network events to a session that doesn't exist yet, and
the bug would be hidden by a separate mechanism.
