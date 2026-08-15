---
why:
  - undisruptive-launch
---

# Splash overlay for loading jank

Not pursued: no user complaint currently motivates it, and it's a
separate problem from focus theft (`040-design.kb/window-control.kb/`)
— a DOM overlay doesn't change OS keyboard routing, it only masks what
paints.

An injected full-viewport DOM overlay, registered via
`page.evaluateOnNewDocument()` (same mechanism as the existing
Done-button overlay in `src/inject.mjs`), can mask a page's real
content until real content is ready, with no flash — proven live
2026-08-14. `removeScriptToEvaluateOnNewDocument(identifier)` scopes
it to the first navigation only, so it doesn't reappear on later
clicks — also proven live.

If picked up: `trash/probe-overlay-splash.mjs` and
`trash/probe-overlay-splash-once.mjs` are the live-verified starting
points (build DOM via `createElement`/`textContent`/inline styles, not
`insertAdjacentHTML`, to stay Trusted-Types-safe without needing the
policy fallback `inject.mjs` uses).
