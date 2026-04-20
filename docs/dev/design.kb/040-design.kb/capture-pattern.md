---
last-updated: "2026-04-20"
why:
  - opaque-extractor-boundary
  - black-box-decomposition
background:
  - har-format
---

# Capture Pattern

**Question.** How does BB1 (the capture stage) pull conversation data out of
a provider's web app?

**Answer.** Network event recording — blanket HAR capture during a
human-driven browsing session. Implemented in `packages/har-browse/` using
Playwright's `recordHar` on a persistent browser context. See
`capture-pattern.kb/network-events.md`.

## Why this one

- **Robust to app refactors.** The app↔server network interface is more
  stable than internal framework state or rendered DOM.
- **Preserves structure.** Conversations-as-JSON survive untouched; fork
  metadata and other non-visible fields are available to BB2.
- **Lean implementation.** Blanket recording means the harness is small; the
  selectivity knowledge lives in the pluck stage (BB2), where it belongs.
- **Policy-safe.** No reverse-engineering of endpoints; the user logs in via
  a real browser session. Aligns with `opaque-extractor-boundary`.

## Alternatives considered

Five patterns were considered. All sit inside the opaque extractor boundary
— the user implements these; assistants do not help with provider-specific
targeting. See `capture-pattern.kb/` for per-pattern detail.

- `inject-ui-read-state.md` — inject UI button, read from app state. Cleanest
  structure preservation but tightest coupling to internals.
- `inject-ui-read-dom.md` — inject UI button, walk the rendered DOM. More
  refactor-stable than state, but lossy on metadata.
- `network-events.md` — **chosen.** Blanket HAR recording via Playwright.
- `raw-cdp.md` — direct CDP session. Lower-level fallback if HAR abstraction
  becomes insufficient.
- `assisted-manual.md` — wizard-guided manual capture. Policy-safest,
  worst UX; held in reserve.
