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

- [~] [claude.ai revisits render from persisted React Query IndexedDB cache](todo.kb/2026-07-22-001-claude-ai-revisits-render-from-persisted-React-Query-IndexedDB-cache--so-capture-sees-no-conversation-traffic.md) — implemented and live-verified on claude.ai 2026-07-26: clearing origin storage turns a cold-load revisit from zero conversation traffic into a full 198KB body, login intact, on consecutive captures. Both directions of the CLI default are pinned by `tests/cli_clear_default.spec.mjs`. Live runs also corrected two beliefs: the per-session `setCacheDisabled`/`setBypassServiceWorker` do *not* address this bug, and entering a conversation by clicking through from Recents fetches anyway (so verification must cold-load the chat URL). Remaining: the same forensic check on chatgpt + aistudio, batched into the live `--howto` session below.
  - [x] Default decided 2026-07-26 (user call): the CLI clears by default, `--keep-origin-storage` opts out; the `startCapture` primitive stays explicit (asymmetry rationale in its doc comment).
- [ ] Batched live `--howto` session (request it per CLAUDE.md Protocols): now ALSO the host migration's tripwire 2 -- a human-driven login on the puppeteer host, watching for bot-challenge/acceptance regressions. Plus the standing items: cold-load a revisited conversation on chatgpt + aistudio and grep for hydration (closes `todo.kb/2026-07-22-001-*`); cold-load the claude.ai index page (open question in devlog `2026-07-26-002`); `navigator.serviceWorker.getRegistrations()` on each provider page -- the forensic pass that prices `todo.kb/2026-07-23-001-*`.
- [x] Reused-profile tab restore (devlog `2026-07-26-003` open question) -- root-caused and fixed 2026-08-14 without needing the live session: this Chromium build defaults `session.restore_on_startup` to "Continue where you left off" even on cleanly-shut-down profiles; `startCapture` now forces it to "Open the New Tab page" on every launch (`disableSessionRestore` in `host_puppeteer.mjs`). Also fixed in the same pass: the UA-metadata probe page opened in the foreground, flashing `file:///`; now backgrounded. Devlog `2026-08-14-000`.
- [ ] [Gate capture-window creation on explicit operator readiness](todo.kb/2026-08-15-000-Gate-capture-window-creation-on-explicit-operator-readiness.md) -- launching `har-browse` steals OS keyboard focus (live-verified 2026-08-14: keystrokes typed elsewhere land in the not-yet-ready window). Every client-side lever tried to prevent the steal failed under this Wayland/Crostini environment, including CDP's own `Target.createTarget({background: true})` -- compositor-owned, not fixable from here. `page.bringToFront()` is not the cause (baseline steals too). Findings: `design.kb/040-design.kb/window-control.kb/`. Proposed fix doesn't need compositor cooperation: gate window creation on an explicit operator keypress.
- [x] Make post-`emit("end")` enqueues loud -- landed 2026-07-26: `enqueue` names each post-end drop on stderr, pinned by `tests/late_enqueue.spec.mjs`. Stderr-only (no throw-in-tests variant: the spec pins the behavior without an env-conditional path). Side benefit: the hung-request drain test now prints its post-grace `loadingFailed` drop -- a visible instance of the loss class the abort-cut todo closes.
- [~] [Migrate capture host to puppeteer-core](todo.kb/2026-07-23-002-Migrate-capture-host-to-puppeteer-core.md) — CORE LANDED 2026-07-26 (devlog `2026-07-26-003`): seam extracted (`capture.mjs` core / `host_playwright.mjs` / `host_puppeteer.mjs`), CLI runs puppeteer-core, UA probe/cache subsystem deleted, playwright demoted to devDeps with an import-graph guard, docs closed. Remaining on the taskfile: tripwire 2 (live login, batched above), `.mjs`→`.ts` fold-in + `devtools-protocol` typing, mutation entries for the new shell.
- [ ] [Zero-miss target coverage via Target.setAutoAttach](todo.kb/2026-07-23-001-Zero-miss-target-coverage-via-Target-setAutoAttach.md) — promoted 2026-07-23 from ideas.kb: service-worker/OOPIF/worker traffic and popups' pre-`Network.enable` window are invisible to per-page sessions. `waitForDebuggerOnStart` closes both classes by construction. Forensic pass batched into the live session above; implementation lands after the host migration above, where auto-attach is a plain API call. The Playwright-transport venue spike is retired 2026-07-26 -- migrate-first answers the venue by fiat.
- [ ] [Replace grace-period drain with abort-based cut at Done](todo.kb/2026-07-23-000-Replace-grace-period-drain-with-abort-based-cut-at-Done.md) — force in-flight requests to real terminal events at the cut instead of waiting out `drainGraceMs`; removes the 2s shutdown floor and the last silent-loss path, supersedes fix 3 below. Event-driven end-to-end: ledger settle + per-session delivery barrier + detach-settlement; no timer in the correctness path. Two CDP spikes gate the mechanism (offline-emulation abort behavior; command/event ordering). Re-ordered 2026-07-26 behind the host migration above: spike 2 verifies a per-transport ordering guarantee and detach-settlement wires the transport's session lifecycle, so building them on the Playwright host ratified for deletion would mean building them twice. Design grounding: `design.kb/030-requirements.kb/capture-cut-completeness.md`, `design.kb/040-design.kb/capture-cut-model.md`.
- [ ] [Done Capturing race drops in-flight requests with no drain](todo.kb/2026-07-22-000-Done-Capturing-race-drops-in-flight-requests-with-no-drain.md) — silent data loss when a slow request hasn't reached `loadingFinished` at click time (2 confirmed victims in the a59dc891 capture). Originally blamed for the zero-conversation-events symptom; re-attributed to the IndexedDB-cache todo above. Fixes 1+2 (extended in-flight tracking + bounded grace-period drain) landed 2026-07-22, mutation-verified, `pnpm test` green. Fix 3 superseded 2026-07-23 by the abort-based-cut todo above. Remaining here: the `has_more=false` discriminator (still needs a capture that actually *reproduces* the truncation -- run 1 of the 2026-07-26 live series paginated cleanly to completion, so it only disproved "no live index capture exists") and the drain-fix signature check, now runnable offline against `trash/live-verify/run*.jsonl`.
- [x] `--headless` redefined 2026-07-28 (user call) as a display *backend* rather than Chromium's mode: `--ozone-platform=headless` plus window/screen sizing. Measured identical to headful on User-Agent, client-hint brands, screen, rAF and GPU, where Chromium's headless mode differs on three of those and Playwright's on four. So the suite is quiet *and* asserts the shipped UA. Record + instrument: `design.kb/040-design.kb/self-identification.kb/headless-changes-the-agent.{md,mjs}`. Internal option is `windowless`, deliberately not `headless`, to avoid collision with puppeteer's.
- [x] `tests/epipe.test.mjs` flake fixed 2026-07-28 by the measured guard change the old entry asked for. Root cause was the 5s guard, not load and not windowing: headed runs measure 4.30/4.31/4.38s and *headless* measured 4.6-4.7s, so headless was slower and 5s was marginal either way. Guard now 15s. Watch for the `newCDPSession: no object with guid page@...` race resurfacing under full-suite load — if it does it is a separate bug, not this budget.
- [x] Suite windows solved 2026-07-28 without xvfb, by the windowless mode above. A virtual display (headless Wayland compositor preferred over Xvfb, to keep Chromium on the same Ozone path as production) remains the fallback if we ever need a configuration with *zero* delta — but the measured delta is currently zero on everything checkable, so there is nothing to buy.
- [ ] `design.kb/070-future-work.kb/capture-implementation-frontier.md`'s `## Comparison Table` (marked `<!-- BEGIN/END GENERATED -->`, instructing "re-run and paste over") is stale against a concurrent-session rewrite of `capture-implementation-frontier.sh`, which no longer emits a markdown table — it emits one YAML document per candidate instead. Decide: keep a generated table (revert the script's output shape) or switch the doc to the YAML-dump shape; then reconcile the doc's instruction and marker comment either way.
- [ ] Two broken links, unrelated to any recent har-browse work, noticed via `llm.kb-validate-links .`: `dev.kb/rust-port.kb/commits.kb/1300-retire-node.md` links up two levels to a sibling of `rust-port.kb/` that isn't there, one level short of where `dev.kb/rust-port.md` actually lives; and `dev.kb/rust-port.kb/handoffs.kb/CLAUDE.md` points at a `commits.kb` entry literally named with an `NNNN` placeholder (probably an intentional template example, not a real dangling link — worth a human glance either way).
- [ ] Tighten `tsconfig.json` once the codebase is ready. Currently `strict: false` and `checkJs: true` (project-wide). Open items: consider enabling `noImplicitAny` once fixture-callback params are typed. (The `playwright-core/lib/server/registry/index` TS7016 stub died with `user-agent.mjs`, 2026-07-26.)
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
