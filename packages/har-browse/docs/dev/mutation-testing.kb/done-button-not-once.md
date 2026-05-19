---
status: done
---

# `inject.mjs`: Done click handler not registered `{ once: true }`

The `dataset.clicked = "true"` write happens on every click. With
`{ once: true }` removed, repeated clicks keep firing the handler.
Mostly idempotent in effect (dataset value is the same), but a future
handler that does non-idempotent work would silently break.

## Injection

`src/inject.mjs`:

```diff
         document.getElementById("capture-done").addEventListener(
           "click",
           (e) => {
             e.target.dataset.clicked = "true";
           },
-          { once: true },
         );
```

## Test Coverage

`tests/persistent_injection.spec.mjs`: "Done click handler is
registered { once: true } and removed after first fire" — new test,
uses CDP `DOMDebugger.getEventListeners` to count click listeners on
`#capture-done` before and after a click. Before: exactly 1. After:
exactly 0 (because `{ once: true }` removes it on fire). Without the
option, the post-fire count stays at 1 — equality fails.

The behavior-observable consequence the mutation puts at risk is "a
future handler doing non-idempotent work fires per-click." The test
asserts the *primitive* (listener removed) rather than the
consequence; that's intentional, since the consequence depends on a
hypothetical future handler change.
