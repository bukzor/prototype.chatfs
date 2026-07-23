---
why:
  - data-possession
  - capture-everything
  - crash-durability
  - unblocked-sessions
---

# What Is the Minimal-Complexity Implementation of BB1 Capture?

Green-field question, decoupled from the current Playwright-based
implementation: if we started over with every language and library in
scope, and quotiented away every historically-contingent commitment
(including the CDP-shaped JSONL record — a convenience of the current
tap point, not a mission requirement), what implementation minimizes
complexity while still satisfying `capture-everything`,
`crash-durability`, and `unblocked-sessions`?

Not currently being pursued — the shipped implementation
(`../050-components.kb/toy-capture.md` and its production analog)
works and is where the effort has gone. Recorded here so a future
rewrite starts from this analysis instead of re-deriving it.

## Two axes, and a third that decides

The obvious tension is **owned code** (what you maintain) vs. **total
footprint** (everything the browser pulls in, held constant across
every candidate since a real browser is unavoidable everywhere). But
ranking candidates on those two axes alone favors designs that look
cheap and quietly drop data. The axis that actually prunes the
candidate set is **silent-miss risk**: how strong is the "if it was
transferred, I have it" guarantee, and would a miss be visible or
silent? An unverifiable miss is a direct failure of
`data-possession`, so it outranks line count.

## Candidates

See `capture-implementation-frontier.kb/` for one file per candidate.
Frontier-optimal rows: no other candidate beats one on every axis at
once. Dominated rows are kept because each is illustrative of a
distinct way a design can look cheap and lose anyway — see the
individual file for the specific veto.

## Comparison Table

Generated from each candidate file's frontmatter by
`capture-implementation-frontier.sh` — re-run it and paste over this
section after adding, removing, or editing a candidate; don't hand-edit
the table itself, or it will drift from the frontmatter it's supposed
to summarize.

<!-- BEGIN GENERATED: capture-implementation-frontier.sh -->
| Candidate | Status | Owned LOC | Middleware | Silent-miss | Crash-durable | Stealth | BB1 purity |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [Thin Wrapper Around the Browser's Own HAR Recorder](capture-implementation-frontier.kb/recordhar-thin-wrapper.md) | frontier-optimal | ~150 | automation framework w/ built-in recorder (e.g. Playwright) | low | poor (written at context close) | good (real browser, spawned) | pure |
| [`puppeteer-core` on a Spawned Browser](capture-implementation-frontier.kb/puppeteer-core-node.md) | frontier-optimal | ~300 | puppeteer-core (Node) | low | good (streamed) | good (real browser, spawned) | pure |
| [Extension Using `chrome.debugger` in the User's Daily Browser](capture-implementation-frontier.kb/browser-extension-tap.md) | frontier-optimal | ~450 | browser extension platform (MV3) | low | good (streamed to a local sink) | perfect (user's own daily browser) | pure |
| [Hand-Rolled CDP Client Over the Debugging Pipe](capture-implementation-frontier.kb/pure-cdp-spawned.md) | frontier-optimal | ~600 | none | low | good (streamed) | good (real browser, spawned) | pure |
| [Manual DevTools "Save as HAR (with Content)"](capture-implementation-frontier.kb/manual-devtools-har.md) | dominated | ~0 | none | low (human error: forgotten preserve-log, missed click) | poor (single manual export, no incremental record) | perfect (user's own browser) | pure |
| [Provider's Official Data Export](capture-implementation-frontier.kb/site-export.md) | dominated | ~50 | none | fatal (fork/tree structure dropped) | n/a (not a live capture) | n/a | leaks all (relies entirely on the provider's export logic) |
| [MITM Proxy (e.g. mitmproxy Addon)](capture-implementation-frontier.kb/mitm-proxy.md) | dominated | ~250 | MITM proxy (e.g. mitmproxy) | medium (cache-served responses invisible) | good (streamed) | poor (proxy's TLS fingerprint, not the browser's) | pure |
| [In-Page `fetch`/XHR Wrapping](capture-implementation-frontier.kb/page-tap-fetch-wrap.md) | dominated | ~250 | none | high (workers, WebSockets, SSE, anything unwrapped) | good (streamed) | perfect (no separate browser instance) | pure-ish (in-page hooks brush against page internals) |
<!-- END GENERATED -->
