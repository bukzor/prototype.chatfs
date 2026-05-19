---
status: done
---

# `inject.mjs`: overlay re-injects on re-navigation

`injectOverlay` is registered as an init script, so it runs again
on every navigation and on every new frame. The early-return on
`document.getElementById("capture-overlay")` makes injection
idempotent. Without it, the overlay duplicates — multiple Done
buttons accumulate, mousedown handlers stack, and the second-onward
button is wired to a stale closure.

## Injection

`src/inject.mjs`:

```diff
       function inject() {
-        if (document.getElementById("capture-overlay")) return;
         const style = document.createElement("style");
```

## Note

Calling-the-name "no-idempotency" turned out to undersell what the
guard is for. Across distinct navigations each document is fresh, so a
single registered init script never duplicates. The mutation only
manifests when **`injectOverlay` is registered twice** on the same
context (two `addInitScript` calls). Both init scripts fire on every
fresh document; without the early-return, each appends its own
overlay.

## Test Coverage

`tests/persistent_injection.spec.mjs`: "injectOverlay is idempotent:
double-register yields one overlay" — new test, calls injectOverlay
twice on the same context, navigates, asserts
`page.locator("#capture-overlay").count()` and `#capture-done` count
are each `1`.
