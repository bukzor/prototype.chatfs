---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    "@value": 2.0
    rationale: |
      File-level estimate for a 5-item rollup: Done-button protocol
      doc, CLAUDE.md refresh, typecheck wiring, @ts-check sweep,
      .mjs→.ts decision. The last is the open-ended item.
  benefit-2w:
    "@value": 1.5
    rationale: |
      Reduces re-orienting cost when returning to har-browse (CLAUDE.md
      is stale). Typecheck catches a class of bugs that currently
      surface at runtime.
  cost-of-delay-2w:
    "@value": 0.3
    rationale: |
      Modest. CLAUDE.md already stale — additional 2w of decay is
      marginal on top of an already-broken orientation. Deferred typecheck
      means runtime-bug class continues to surface (~1 incident/2w
      cost ≈ 0.3 SWEh). No external dollar flow or deadline.
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
- [ ] Wire build-time typecheck (prerequisite for the next item to have real rigor). Install `typescript` as a devDep, add `tsconfig.json` at package root (`allowJs: true`, `checkJs: false` so `@ts-check` opts in per-file, `noEmit: true`, `strict: true`, `module: nodenext`, `target: esnext`, include `src/**/*.mjs` and `tests/**/*.mjs`), add `"typecheck": "tsc -p ."` to `package.json` scripts, wire into CI. Without this, `@ts-check` is editor-only — no CI gate.
- [ ] Add `// @ts-check` to remaining `.mjs` files (`src/cache.mjs`, `src/cdp_to_har.mjs`, `src/har_browse.mjs`, `src/inject.mjs`, `src/playwright.mjs`, `src/user-agent.mjs`, tests). Per-file opt-in; tighten any errors that surface. Depends on the typecheck wiring above for real rigor.
- [ ] Rename `.mjs` → `.ts` for native TS syntax. Node 22 strips types from `.ts` by default, so `#!/usr/bin/env node` shebangs work unchanged — just avoid `enum`/`namespace`/parameter-properties (the runtime-emitting TS constructs) or accept switching to `tsx`. Playwright loads `.ts` natively, so tests need no runner change. Consider installing `devtools-protocol` for typed CDP event shapes (would let us drop `any` on `params` throughout `capture.mjs`).

## Done

- [x] [har-browse streaming refactor](todo.kb/2026-04-24-000-har-browse-streaming-refactor.md) — superseded by the public-events refactor.
- [x] [pw-browse public-events stream](todo.kb/2026-04-24-001-pw-browse-public-events-stream.md)
- [x] [cdp2har: validate chrome-har consumes our stream](todo.kb/2026-04-24-002-cdp2har-validate-chrome-har-consumes-our-stream.md)
- [x] [har-browse: handle EPIPE on stdout cleanly](todo.kb/2026-04-24-003-har-browse-handle-epipe-on-stdout-cleanly.md)
