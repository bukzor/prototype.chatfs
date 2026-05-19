---
status: done
---

# `capture.mjs`: Done poll watches the wrong dataset key

`waitForFunction` checks `dataset.clicked === "true"`. A typo
(`.click`, `.clickeed`, etc.) decouples the poll from the inject
handler, and Done click never terminates capture — process hangs
until the context closes.

## Injection

`src/capture.mjs`, in the `done` Promise.race:

```diff
     page.waitForFunction(
-      () => document.getElementById("capture-done")?.dataset.clicked === "true",
+      () => document.getElementById("capture-done")?.dataset.click === "true",
     ),
```

## Test Coverage

`tests/har.spec.mjs` (and every other capture-driven spec): clicks the
Done button and awaits `session.events`. With the typo, Done click no
longer terminates the capture; tests hang and Playwright's timeout
fires, producing a hard failure.
