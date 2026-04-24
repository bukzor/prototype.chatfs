<anthropic-skill-ownership llm-subtask />

# Tactical Tasks

- [x] [har-browse streaming refactor](todo.kb/2026-04-24-000-har-browse-streaming-refactor.md) — `captureHar` is now an async generator; `har-browse` streams JSONL to stdout. **Superseded** by the public-events refactor below: HAR-entry was the wrong seam.
- [x] [pw-browse public-events stream](todo.kb/2026-04-24-001-pw-browse-public-events-stream.md) — replaced HAR-entry stream with a **CDP event passthrough** in chrome-har's `{method, params}` shape. Bodies attached at `Network.responseReceived.params.response.body`. `har-browse` bin unchanged; `captureHar` → `captureEvents`; `src/playwright/` deleted.
- [ ] [cdp2har: validate chrome-har consumes our stream](todo.kb/2026-04-24-002-cdp2har-validate-chrome-har-consumes-our-stream.md) — claim is structural; needs an end-to-end smoke test plus a ~20-line wrapper around `harFromMessages`.
- [ ] [har-browse: handle EPIPE on stdout cleanly](todo.kb/2026-04-24-003-har-browse-handle-epipe-on-stdout-cleanly.md) — piping to `head` / early-exiting consumers currently dumps a Node stack trace. Add stdout error guard.

## Deferred

- [ ] Rename package `har-browse` → something honest (`pw-browse`?). Cross-cuts package.json, workspace, docs, devlog refs.
- [ ] `--wait-response` (originally split out of streaming refactor): with events as the seam, becomes "wait for an event matching a pattern". Small CLI feature on top of the new generator.
