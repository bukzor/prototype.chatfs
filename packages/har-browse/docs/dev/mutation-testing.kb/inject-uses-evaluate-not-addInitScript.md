---
status: done
---

# `inject.mjs`: `addInitScript` replaced with one-shot `evaluate`

`injectOverlay` uses `page.addInitScript`, which fires on every fresh
document load — overlay re-appears after every navigation. Replace
with `page.evaluate` and the overlay only injects on the current
document; the next navigation loses it, and the Done button vanishes
mid-session.

## Injection

`src/inject.mjs`:

```diff
-  await page.addInitScript(
+  await page.evaluate(
     ({ html, css, howto }) => {
```

## Test Coverage

`tests/persistent_injection.spec.mjs` — all three tests fail
deterministically with the mutation:
- "Done Capturing button survives navigations"
- "Done click handler is registered { once: true } and removed after first fire"
- "injectOverlay is idempotent: double-register yields one overlay"

`page.evaluate` runs against the current document only; the very next
`page.goto(...)` lands on a fresh document with no overlay
(`#capture-overlay` count is 0), and every persistence-oriented
assertion in the suite fails.
