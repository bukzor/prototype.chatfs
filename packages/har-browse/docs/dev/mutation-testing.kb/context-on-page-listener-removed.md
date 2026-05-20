---
status: done
---

# `capture.mjs`: `context.on("page", ...)` removed — new pages not wired

`attachCapture` wires the initial page synchronously, then registers
`context.on("page", (p) => track(wireSession(p)))` to wire any page
opened later (popup, `target=_blank`, programmatic `context.newPage()`).
Drop the listener and CDP events for those pages never reach the
emitter — Network/Runtime/Page activity on the new page is silent.

## Injection

`src/capture.mjs`:

```diff
   await wireSession(page);
-  context.on("page", (p) => track(wireSession(p)));
```

## Fixture needed

Test that opens a second page via `context.newPage()` (or via a page-side
`window.open`), issues a fetch from it, and asserts the captured event
stream contains a `Network.responseReceived` with that page's
requestId. With the listener removed, the assertion fails (no events
from the second page).
