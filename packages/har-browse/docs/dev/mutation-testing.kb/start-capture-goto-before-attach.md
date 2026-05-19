---
status: todo
---

# `capture.mjs`: `startCapture` navigates before attaching CDP

`startCapture` carefully calls `attachCapture(page)` (which wires the
CDP session synchronously via `await wireSession(page)`) *before*
`page.goto(url)`. Swap the order and the navigation fires before
CDP is listening — the initial document's `Network.requestWillBeSent`
/ `responseReceived` events are lost, so chrome-har sees a HAR with no
initial page load entry.

## Injection

`src/capture.mjs`, in `startCapture`:

```diff
-  const { events, done } = await attachCapture(page, { howto });
   await page.goto(url, { waitUntil: "commit" });
+  const { events, done } = await attachCapture(page, { howto });
```

## Fixture needed

Test asserts the captured stream contains a `Network.responseReceived`
whose `request.url` ends with the toy-server origin (the initial nav).
Without the original ordering, that event fires before CDP attaches
and the assertion fails (count: 0).
