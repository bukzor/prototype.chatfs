---
status: todo
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

## Hypothesis

`tests/persistent_injection.spec.mjs` ("Done Capturing button survives
navigations") navigates three times and asserts
`page.locator("#capture-done").count() === 1` after each. With
`page.evaluate` (one-shot), the second navigation lands on a fresh
document with no overlay — count is 0 and the assertion fails. Drive
through inject→test→revert to confirm and link the test.
