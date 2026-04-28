<anthropic-skill-ownership llm-subtask />

# Tactical Tasks

- [x] [har-browse streaming refactor](todo.kb/2026-04-24-000-har-browse-streaming-refactor.md) — `captureHar` is now an async generator; `har-browse` streams JSONL to stdout. **Superseded** by the public-events refactor below: HAR-entry was the wrong seam.
- [x] [pw-browse public-events stream](todo.kb/2026-04-24-001-pw-browse-public-events-stream.md) — replaced HAR-entry stream with a **CDP event passthrough** in chrome-har's `{method, params}` shape. Bodies attached at `Network.responseReceived.params.response.body`. `har-browse` bin unchanged; `captureHar` → `captureEvents`; `src/playwright/` deleted.
- [x] [cdp2har: validate chrome-har consumes our stream](todo.kb/2026-04-24-002-cdp2har-validate-chrome-har-consumes-our-stream.md) — added `cdp-to-har` bin (~20 lines) + `test_e2e_har.mjs` driving `captureEvents → harFromMessages` against the toy server. Claim is now empirical: entries, pages, timings, and the `/api/conversation` body round-trip through chrome-har unmodified.
- [x] [har-browse: handle EPIPE on stdout cleanly](todo.kb/2026-04-24-003-har-browse-handle-epipe-on-stdout-cleanly.md) — stdout error handler sets a flag; loop breaks and the generator's `finally` closes the context. `test_epipe.mjs` verifies the pattern (clean exit, no stack trace) via a `sed -n 1,1p` consumer.

