---
status: todo
---

# `capture.mjs`: `awaitingBody` map shared across CDP sessions

Currently declared inside `wireSession` — each per-page CDP session
owns its own `awaitingBody`. Hoist it to `attachCapture` scope and the
map becomes shared across sessions. CDP requestIds are unique per
session, not globally; collisions between pages cause an LF from page A
to look up an RR stashed by page B, attaching the wrong body and
silently corrupting the capture.

## Injection

`src/capture.mjs`:

```diff
   const emitter = new EventEmitter();
   const queue = on(emitter, "event", { close: ["end"] });
+  /** @type {Map<string, any>} */
+  const awaitingBody = new Map();

   /** @param {Page} subject */
   const wireSession = async (subject) => {
     const session = await context.newCDPSession(subject);
-    /** @type {Map<string, any>} */
-    const awaitingBody = new Map();
```

## Fixture needed

Two-page capture where both pages issue a request that happens to share
a CDP requestId (engineered by counting CDP messages or by stalling one
session's RR until the other session emits an LF). Assert each page's
RR body matches the URL it was fetched from. Possibly **gap** —
requires precise CDP-id manipulation that may not be reproducible
without intercepting CDP.
