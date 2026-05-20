---
status: gap
attempts: 1
---

# `capture.mjs`: `injectOverlay(page, ...)` not awaited

`page.addInitScript()` returns a Promise — the script isn't actually
registered until it resolves. Drop the `await` and `attachCapture`
proceeds to set up the Done barrier before the init script is in
place; the next `page.goto()` (in `startCapture`) navigates before the
overlay registration completes, so the Done button never appears for
the first page load. Subsequent navigations would still get the
overlay (the addInitScript eventually lands).

## Injection

`src/capture.mjs`:

```diff
-  await injectOverlay(page, { howto });
+  injectOverlay(page, { howto });
```

## Test Result

Marked gap after running the full playwright suite (14 tests) with the
bug injected — all passed, including 5 repeats of `popup_page.spec.mjs`.

Analysis: `page.addInitScript` and `page.goto` both go through the same
Playwright channel → CDP transport, and Playwright issues their CDP
commands in code order (`Page.addScriptToEvaluateOnNewDocument` then
`Page.navigate`). Chromium processes CDP messages serially in receive
order, so the script is registered before the navigation creates the
new document — regardless of whether the *client* awaits the ACK. The
client-side Promise we'd be awaiting only confirms a server roundtrip
that has, on the wire, already happened in the right order.

Dropping the `await` may matter for code clarity / unhandled rejection
hygiene, but the runtime ordering invariant doesn't depend on it.

## See Also

`barrier-promise-not-tracked` — similar analysis class (microtask FIFO
preserves observable order; client-side await is dead defense).
