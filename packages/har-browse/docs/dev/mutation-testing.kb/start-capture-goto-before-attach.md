---
status: done
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

## Test Coverage

`tests/initial_nav.spec.mjs` — "initial navigation RR is captured" —
runs `startCapture` against the toy server, ends the stream via
`context.close()` (overlay-independent, since the bug also breaks the
overlay), and asserts a `Network.responseReceived` event for the root
URL is present in the captured stream. With the bug, the initial nav
fires before CDP listeners attach and the RR is missing.
