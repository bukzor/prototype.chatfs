---
managed-by: Skill(llm-subtask)
cost-benefit-sweh:
  timebox:
    "@value": 1.0
    rationale: |
      File-level estimate for the remaining rollup: .mjs→.ts decision
      (open-ended), tsconfig tightening (small). CLAUDE.md refresh and
      the Done-button protocol doc landed 2026-07-26.
  benefit-2w:
    "@value": 1.0
    rationale: |
      Reduces re-orienting cost when returning to har-browse. Typecheck
      now wired (041b31e) — that bug class is gated.
  cost-of-delay-2w:
    "@value": 0.2
    rationale: |
      Modest. CLAUDE.md stale — additional 2w of decay is marginal on
      top of an already-broken orientation. Typecheck wired so its
      runtime-bug class is now caught.
    confidence: tentative
---

# Tactical Tasks

> This file is for tracking *open work*, not recording how a fix was
> found or verified — that's devlog content. Put reasoning, root-cause
> analysis, and rejected alternatives in `docs/dev/devlog/`
> (`llm-collab-devlog --title "..."`) and leave only a short pointer
> here.

- [ ] `tests/epipe.test.mjs` ("har-browse | head -n 1 exits cleanly") is flaky under full-suite parallel load: intermittently throws `browserContext.newCDPSession: page: no object with guid page@...` (Playwright internal race), ~1-in-3 to ~1-in-5 in this session's `pnpm test` runs. Passes reliably standalone (confirmed on both the pre- and post-2026-07-22-drain-race-fix tree, so it predates and is unrelated to that fix). Not investigated further this session — root cause likely resource contention (many concurrent Chromium instances) rather than a real bug, but unconfirmed.
- [~] [claude.ai revisits render from persisted React Query IndexedDB cache](todo.kb/2026-07-22-001-claude-ai-revisits-render-from-persisted-React-Query-IndexedDB-cache--so-capture-sees-no-conversation-traffic.md) — implemented and live-verified on claude.ai 2026-07-26: `--clear-origin-storage` turns a cold-load revisit from zero conversation traffic into a full 198KB body, login intact, on consecutive captures. Live runs also corrected two beliefs: the per-session `setCacheDisabled`/`setBypassServiceWorker` do *not* address this bug, and entering a conversation by clicking through from Recents fetches anyway (so verification must cold-load the chat URL). Remaining: the same forensic check on chatgpt + aistudio (ask-first), and the decision below.
  - [ ] Decide whether `--clear-origin-storage` should default ON. Recommendation: yes for chatfs provider flows — without it a cold-load claude.ai capture is silently empty of its payload, which is the exact failure the mission forbids. Cost is a slower load and the loss of locally-stored drafts. Left off pending the user's call.
- [ ] [Replace grace-period drain with abort-based cut at Done](todo.kb/2026-07-23-000-Replace-grace-period-drain-with-abort-based-cut-at-Done.md) — force in-flight requests to real terminal events at the cut instead of waiting out `drainGraceMs`; removes the 2s shutdown floor and the last silent-loss path, supersedes fix 3 below. Event-driven end-to-end: ledger settle + per-session delivery barrier + detach-settlement; no timer in the correctness path. Two CDP spikes gate the mechanism (offline-emulation abort behavior; command/event ordering). While in this code, extract the host seam (CDP sessions/events behind one interface) — precondition for the host-migration todo below. Design grounding: `design.kb/030-requirements.kb/capture-cut-completeness.md`, `design.kb/040-design.kb/capture-cut-model.md`.
- [ ] [Zero-miss target coverage via Target.setAutoAttach](todo.kb/2026-07-23-001-Zero-miss-target-coverage-via-Target-setAutoAttach.md) — promoted 2026-07-23 from ideas.kb: service-worker/OOPIF/worker traffic and popups' pre-`Network.enable` window are invisible to per-page sessions. `waitForDebuggerOnStart` closes both classes by construction. First steps: forensic pass for SW payload serving (prices urgency), venue spike (Playwright transport vs raw CDP connection vs rust port). Ratified 2026-07-23: a can't-carry verdict escalates the host-migration todo below to immediate priority.
- [ ] [Migrate capture host to puppeteer-core](todo.kb/2026-07-23-002-Migrate-capture-host-to-puppeteer-core.md) — ratified 2026-07-23 frontier review: the current Playwright host is off the requirement-weighted frontier (largest middleware footprint of any candidate; ~180 owned lines exist only to fight it — UA probe/cache subsystem, launch workarounds, popup-race wiring). Swap launcher/profile/transport to puppeteer-core behind the host seam above; keep Playwright as a devDependency for the test suite only. Gated on the seam (todo above) and triggered/timed by the auto-attach venue spike (todo above).
- [ ] [Done Capturing race drops in-flight requests with no drain](todo.kb/2026-07-22-000-Done-Capturing-race-drops-in-flight-requests-with-no-drain.md) — silent data loss when a slow request hasn't reached `loadingFinished` at click time (2 confirmed victims in the a59dc891 capture). Originally blamed for the zero-conversation-events symptom; re-attributed to the IndexedDB-cache todo above. Fixes 1+2 (extended in-flight tracking + bounded grace-period drain) landed 2026-07-22, mutation-verified, `pnpm test` green. Fix 3 superseded 2026-07-23 by the abort-based-cut todo above. Remaining here: the `has_more=false` discriminator and live-capture validation, both blocked on a fresh live capture (ask-first).
- [ ] `design.kb/070-future-work.kb/capture-implementation-frontier.md`'s `## Comparison Table` (marked `<!-- BEGIN/END GENERATED -->`, instructing "re-run and paste over") is stale against a concurrent-session rewrite of `capture-implementation-frontier.sh`, which no longer emits a markdown table — it emits one YAML document per candidate instead. Decide: keep a generated table (revert the script's output shape) or switch the doc to the YAML-dump shape; then reconcile the doc's instruction and marker comment either way.
- [ ] Two broken links, unrelated to any recent har-browse work, noticed via `llm.kb-validate-links .`: `dev.kb/rust-port.kb/commits.kb/1300-retire-node.md` links up two levels to a sibling of `rust-port.kb/` that isn't there, one level short of where `dev.kb/rust-port.md` actually lives; and `dev.kb/rust-port.kb/handoffs.kb/CLAUDE.md` points at a `commits.kb` entry literally named with an `NNNN` placeholder (probably an intentional template example, not a real dangling link — worth a human glance either way).
- [ ] Tighten `tsconfig.json` once the codebase is ready. Currently `strict: false` and `checkJs: true` (project-wide). Open items: declare a stub for `playwright-core/lib/server/registry/index` to silence TS7016; consider enabling `noImplicitAny` once fixture-callback params are typed.
- [ ] Rename `.mjs` → `.ts` for native TS syntax — folded into [Migrate capture host to puppeteer-core](todo.kb/2026-07-23-002-Migrate-capture-host-to-puppeteer-core.md) (touches every integration point anyway). Node 22 strips types from `.ts` by default, so `#!/usr/bin/env node` shebangs work unchanged — just avoid `enum`/`namespace`/parameter-properties (the runtime-emitting TS constructs) or accept switching to `tsx`. Playwright loads `.ts` natively, so tests need no runner change. Consider installing `devtools-protocol` for typed CDP event shapes (would let us drop `any` on `params` throughout `capture.mjs`).

## Mutation testing

Kb at `docs/dev/mutation-testing.kb/` — directory listing (and each
file's `status:` frontmatter) is the index, not restated here. Original
terminus session: `~/.claude/sessions.kb/har-browse-mutation-testing.md`.

The terminus-era gaps are all analyzed-unreachable / dead-defense
(`## Test Result` in each file explains why hardening is impractical):
`awaiting-body-not-deleted`, `awaiting-body-shared-across-sessions`,
`barrier-payload-no-optional-chaining`, `barrier-promise-not-tracked`,
`barrier-snapshot-not-frozen`, `body-attached-after-loading-finished`,
`context-close-no-stream-end`, `inject-overlay-not-awaited`.

Entries filed 2026-07-22 were prospective. The fix-1/2-scoped subset
was burned down 2026-07-22 (`status: done`). The four fix-3-scoped
entries (`drain-expiry-flush-*`, `truncation-marker-set-unconditionally`)
were deleted 2026-07-23 — fix 3 was superseded by the abort-based cut
(`todo.kb/2026-07-23-000-*`), which lists their carried-forward intents
and re-files per `Skill(mutation-testing)` at implementation. The
`clearOriginStorage`-scoped entries were burned down 2026-07-26
alongside `todo.kb/2026-07-22-001-*` (all `done`), joined by two new
`session-*` entries for the per-session capture settings.

## Done

- [x] [har-browse streaming refactor](todo.kb/2026-04-24-000-har-browse-streaming-refactor.md) — superseded by the public-events refactor.
- [x] [pw-browse public-events stream](todo.kb/2026-04-24-001-pw-browse-public-events-stream.md)
- [x] [cdp2har: validate chrome-har consumes our stream](todo.kb/2026-04-24-002-cdp2har-validate-chrome-har-consumes-our-stream.md)
- [x] [har-browse: handle EPIPE on stdout cleanly](todo.kb/2026-04-24-003-har-browse-handle-epipe-on-stdout-cleanly.md)
- [x] Wire build-time typecheck — `tsc --noEmit` as a `node:test` (commit 041b31e). Took the project-wide `checkJs: true` path instead of per-file `@ts-check`, which subsumes the planned `@ts-check` sweep.
- [x] `#capture-done` overlay invisible on aistudio.google.com — Trusted Types CSP blocked `insertAdjacentHTML`. Fixed and user-confirmed live. See devlog `docs/dev/devlog/2026-07-23-000-har-browse-Done-button-invisible-on-aistudio-google-com--Trusted-Types-.md`.
- [x] Refresh `CLAUDE.md` — landed 2026-07-26: full rewrite (BB1 framing, `attachCapture`/`startCapture` split, Done-button + BARRIER protocols with `tests/barrier_consumed.spec.mjs` pointer, `ideas.kb` cross-link, dead `data/` artifact reference dropped, puppeteer-core-migration warning, Current Work section). The paired `src/capture.mjs` BARRIER header comment landed same day (initially deferred to dodge a concurrent-edit clobber).
- [x] Document the Done-button protocol in a `src/inject.mjs` header comment (DOM-dataset signal, and why not a `harBrowseMark` binding or CDP event).
