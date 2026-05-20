---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    "@value": 1.5
    rationale: |
      File-level estimate for the remaining rollup: Done-button protocol
      doc, CLAUDE.md refresh, .mjs→.ts decision (open-ended), tsconfig
      tightening (small).
  benefit-2w:
    "@value": 1.0
    rationale: |
      Reduces re-orienting cost when returning to har-browse (CLAUDE.md
      still stale). Typecheck now wired (041b31e) — that bug class is
      gated.
  cost-of-delay-2w:
    "@value": 0.2
    rationale: |
      Modest. CLAUDE.md stale — additional 2w of decay is marginal on
      top of an already-broken orientation. Typecheck wired so its
      runtime-bug class is now caught.
    confidence: tentative
---

# Tactical Tasks

- [ ] Add a header comment to `src/inject.mjs` documenting the Done-button protocol: page injects `#capture-done`, click handler sets `dataset.clicked = "true"`, capture polls via `page.waitForFunction(… dataset.clicked === "true")` in `capture.mjs`. Note the choice (DOM-dataset, not `harBrowseMark("DONE")` or a CDP signal) so 6-month-you doesn't re-litigate it.
- [ ] Refresh `CLAUDE.md` so 6-month-future-you isn't bewildered.
  - [ ] Update "Key Files" entry for `capture.mjs`: drop stale `captureEvents()` reference; describe current `attachCapture(page)` (low-level) vs `startCapture(opts)` (convenience wrapper) split.
  - [ ] Document the BARRIER protocol, paired in two places so it's reachable where you'd look:
    - `CLAUDE.md`: short paragraph — page-side `window.harBrowseMark("BARRIER:…")` carries a page-attested consumed list; capture defers each BARRIER's emit until in-flight body-fetches settle, so consumed RRs precede the BARRIER that names them. Point at `tests/barrier_consumed.spec.mjs` as the formal invariant.
    - `src/capture.mjs`: header comment with the mechanic detail (snapshot-via-spread of `inFlight`, `allSettled`-superset ordering for concurrent BARRIERs) and a pointer to the same test.
  - [ ] Cross-link to `.claude/ideas.kb/` for deferred work, especially the streaming-witness gate idea.
  - [ ] Verify references to `toy_server/`, `toy_pluck.sh`, etc. still match the tree; remove or update stale paths.
- [ ] Tighten `tsconfig.json` once the codebase is ready. Currently `strict: false` and `checkJs: true` (project-wide). Open items: declare a stub for `playwright-core/lib/server/registry/index` to silence TS7016; consider enabling `noImplicitAny` once fixture-callback params are typed.
- [ ] Rename `.mjs` → `.ts` for native TS syntax. Node 22 strips types from `.ts` by default, so `#!/usr/bin/env node` shebangs work unchanged — just avoid `enum`/`namespace`/parameter-properties (the runtime-emitting TS constructs) or accept switching to `tsx`. Playwright loads `.ts` natively, so tests need no runner change. Consider installing `devtools-protocol` for typed CDP event shapes (would let us drop `any` on `params` throughout `capture.mjs`).

## Mutation testing (paused 2026-05-20)

Kb at `docs/dev/mutation-testing.kb/` (53 entries). Status:
45 done, 7 gap, 1 todo. Session record:
`~/.claude/sessions.kb/har-browse-mutation-testing.md`.

- [ ] Drive remaining 1 todo through inject→test→revert:
  `awaiting-body-shared-across-sessions` — requires engineered CDP
  requestId collision across two pages. Likely **gap** without CDP
  interception.
- [ ] Re-attempt 2 recoverable gaps:
  - `barrier-promise-not-tracked` — adversarial-delay BARRIER FIFO
    fixture (mixed `?delay=N`). Analysis suggests microtask FIFO +
    shared-LF snapshots may make `track()` a no-op for ordering; the
    track may actually be Done-drain insurance, not serialization.
    Re-run with mutation injected showed full BARRIER suite passes —
    so the order invariant isn't what `track()` protects in practice.
  - `body-attached-after-loading-finished` — per-request RR-before-LF
    JSONL-index assertion across captured stream.
- [ ] 5 remaining gaps are analyzed-unreachable / dead defense:
  `awaiting-body-not-deleted`, `barrier-payload-no-optional-chaining`,
  `barrier-snapshot-not-frozen`, `context-close-no-stream-end`,
  `inject-overlay-not-awaited`. Each has a `## Test Result` body
  explaining why hardening is impractical.

## Done

- [x] [har-browse streaming refactor](todo.kb/2026-04-24-000-har-browse-streaming-refactor.md) — superseded by the public-events refactor.
- [x] [pw-browse public-events stream](todo.kb/2026-04-24-001-pw-browse-public-events-stream.md)
- [x] [cdp2har: validate chrome-har consumes our stream](todo.kb/2026-04-24-002-cdp2har-validate-chrome-har-consumes-our-stream.md)
- [x] [har-browse: handle EPIPE on stdout cleanly](todo.kb/2026-04-24-003-har-browse-handle-epipe-on-stdout-cleanly.md)
- [x] Wire build-time typecheck — `tsc --noEmit` as a `node:test` (commit 041b31e). Took the project-wide `checkJs: true` path instead of per-file `@ts-check`, which subsumes the planned `@ts-check` sweep.
