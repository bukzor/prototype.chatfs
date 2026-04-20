# Raw CDP Capture

Attach a `CDPSession` directly and subscribe to DevTools-level network events.
Bypasses Playwright's HAR abstraction for lower-level access to the underlying
Chrome DevTools Protocol.

**Pros.** Access to events that don't surface through Playwright's high-level
API (early-stage requests, pre-render navigation, service worker traffic).
More control over timing and filtering.

**Cons.** Lower-level, more code, more ways to break. Playwright's HAR
recording (`network-events.md`) is a purpose-built wrapper that solves the
common case; CDP is a fallback when that's insufficient.
