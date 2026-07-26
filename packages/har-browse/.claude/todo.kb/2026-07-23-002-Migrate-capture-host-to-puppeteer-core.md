---
managed-by: Skill(llm-subtask)
required-reading:
  - packages/har-browse/design.kb/070-future-work.kb/capture-implementation-frontier.md
  - packages/har-browse/design.kb/050-components.kb/toy-capture.md
  - packages/har-browse/src/capture.mjs
suggested-reading:
  - packages/har-browse/design.kb/070-future-work.kb/capture-implementation-frontier.kb/puppeteer-core-node.md
  - packages/har-browse/.claude/todo.kb/2026-07-23-001-Zero-miss-target-coverage-via-Target-setAutoAttach.md
  - packages/har-browse/src/playwright.mjs
  - packages/har-browse/src/user-agent.mjs
cost-benefit-sweh:
  timebox:
    "@value": 3.0
    rationale: |
      Deletion-heavy once the host seam exists (landed with
      2026-07-23-000): the swap replaces launcher/profile/transport and
      deletes the UA probe/cache subsystem, launch workarounds, and
      popup-race machinery. Long poles: browser-executable acquisition
      (puppeteer-core bundles no browser), .ts fold-in, mutation
      re-file for the new shell.
    confidence: tentative
  benefit-2w:
    "@value": 0.7
    rationale: |
      Deletes the ~180-line Playwright-fight stratum and the largest
      middleware footprint of any frontier candidate; converts
      auto-attach (2026-07-23-001) from spike-gated to a plain API
      call. No user-visible capture behavior change by itself — the
      value is unblocking and simplification.
    confidence: confident
  cost-of-delay-2w:
    "@value": 0.5
    rationale: |
      Ungated since the 2026-07-26 re-ordering: the abort cut and the
      auto-attach implementation (a completeness requirement) both
      queue behind this migration, and every week on the Playwright
      host invites more code shaped around it.
    confidence: tentative
---

# Migrate capture host to puppeteer-core; demote Playwright to dev/test-only

**Priority:** High -- next major work item (2026-07-26 re-ordering): the abort-based cut and the auto-attach implementation both queue behind it; only the venue-independent todo.md quick items precede it.
**Complexity:** Medium — shell-only swap behind the capture-semantics seam; risk concentrates in launch/profile parity and browser acquisition.
**Context:** Ratified 2026-07-23 frontier plan (survey: `design.kb/070-future-work.kb/capture-implementation-frontier.md`). The current Playwright host is off the frontier: largest middleware footprint of any candidate, with ~180 owned lines existing only to fight it (UA probe/cache subsystem, `playwright.mjs` launch workarounds, popup-attach race machinery), while its page-automation value goes unused in production (the human drives). Both open completeness todos already route around it.

## Problem Statement

Playwright serves three production roles — launcher, profile manager,
CDP transport — all replaceable by a small CDP library, and it obstructs
the next requirement-driven change: `Target.setAutoAttach` with
`waitForDebuggerOnStart` may conflict with Playwright's own attach
machinery (the venue spike in `2026-07-23-001-*` existed to find out;
retired 2026-07-26 as moot under migrate-first).
Meanwhile the framework forces owned workarounds: pre-launch UA
cache/probe (`user-agent.mjs` + `cache.mjs`), Crostini launch fights
(`playwright.mjs`), and reactive `context.on("page")` wiring with its
popup race.

## Proposed Solution

Swap the host shell to `puppeteer-core` (library-mediated raw CDP on a
spawned browser — the frontier's requirement-weighted winner), keeping
the venue-agnostic capture semantics (ledger/drain/barrier/overlay)
unchanged behind the host seam. Playwright remains a devDependency for
the test suite, where page automation is the actual job.

**Re-ordered 2026-07-26:** this migration is next -- no trigger, no
gate. The `2026-07-23-001-*` venue spike that formerly timed it is
retired (migrate-first answers the venue by fiat). The abort-based cut
(`2026-07-23-000-*`) is sequenced behind it because the cut's delivery
barrier and detach-settlement are transport-sensitive and should be
built once, against the host that ships; the host seam is extracted as
this migration's first step rather than inherited from the cut work.

## Implementation Steps

- [x] **Extract the host seam** as the migration's first move (step
      moved here 2026-07-26 from `2026-07-23-000-*`): capture semantics
      consume "CDP sessions + events per target" through one small
      interface, so the swap below is a shell replacement. The
      abort-based cut, now sequenced after this migration, consumes the
      same seam. Landed 2026-07-26: `src/capture.mjs` is the
      venue-agnostic core (`captureStream(host)` over a `CaptureHost`
      typedef: `initialTarget`/`onTarget`/`session(target)`/`cut`);
      `src/host_playwright.mjs` is the shell (`attachCapture`/
      `startCapture` moved verbatim, emit-override session adaptation,
      overlay + cut race). Full suite green, zero behavior change.
- [~] **Tripwires next (the only ways this migration aborts; entry is
      unconditional):** smoke-launch puppeteer-core on Crostini --
      persistent profile, headed, CDP attach, UA override -- before any
      wholesale swap; then, first time a page is up, a human-driven
      login to one real provider (`--howto` policy) to check for
      bot-challenge/acceptance regressions the Playwright workarounds
      may have been masking. Either failing reverts to the Playwright
      shell behind the seam; the seam still lands either way.
  - [x] Tripwire 1 (Crostini smoke) PASSED 2026-07-26
        (`trash/puppeteer-smoke.mjs`, puppeteer-core 25.3.0 driving
        Playwright's Chromium 147): headed launch + `userDataDir`
        profile OK; `createCDPSession` OK; mitt-style `'*'` wildcard
        delivers blanket events (emit-override hack unnecessary);
        `Browser.getVersion` + `Network.setUserAgentOverride`
        round-trips (UA probe/cache subsystem deletable);
        `defaultViewport: null` uses real window size (1018x791);
        `ignoreDefaultArgs: ["--enable-automation"]` +
        `--disable-blink-features=AutomationControlled` give
        `navigator.webdriver === false`; cookies persist across
        relaunch. Wrinkle: a reused profile session-restored the prior
        run's tabs (3 initial pages) -- the port must pin initial-page
        selection and consider crash-restore suppression.
  - [ ] Tripwire 2 (human-driven real-provider login) -- pending the
        swap producing a runnable capture; batch into the standing live
        `--howto` session (todo.md).
- [ ] Decide browser acquisition: puppeteer-core bundles no browser.
      Candidates: keep Playwright's Chromium (already a devDependency;
      resolve via its registry as today), system Chrome, or
      `@puppeteer/browsers`. Weigh against `unblocked-sessions`
      (revision pinning affects fingerprint stability).
- [ ] Swap launcher/profile/transport: `puppeteer.launch({executablePath,
      userDataDir, headless: false})`; port the per-profile
      `${XDG_CACHE_HOME}/har-browse/profile/${profile}` layout unchanged.
- [x] Replace the UA subsystem with `Browser.getVersion` +
      `Network.setUserAgentOverride`; delete `user-agent.mjs`,
      `cache.mjs`, their tests; retire the `ua-*`/`cache-*` mutation
      entries whose target code is gone. Landed 2026-07-26, two
      deviations: `cache.mjs` STAYS (its `cachePath` serves the CLI's
      profile dirs -- only the UA cache usage died) with its
      `cachePath`-scoped mutation entries; and the swap trades away
      launch-time whole-context UA branding for per-attached-session
      override, leaving popup-first-request/non-page-target traffic
      unbranded until auto-attach (`2026-07-23-001-*`) closes that
      window by construction (user-ratified this trade 2026-07-26).
      13 UA-scoped mutation entries deleted; UA-suffix correctness
      re-files against the new shell under the mutation step below.
- [ ] Delete `playwright.mjs` launch workarounds; verify on Crostini
      that a plain launch doesn't reintroduce them (the viewport
      override and SwiftShader flag were Playwright defaults, not
      Chromium's).
- [ ] Replace `context.on("page")` wiring; `2026-07-23-001-*`
      implements auto-attach in this venue (its natural shape), which
      supersedes the popup-race machinery and `popup_race.spec.mjs`'s
      workaround posture.
- [ ] Keep Playwright as devDependency; assert the production import
      graph is playwright-free (cheap `node:test` walking `src/`
      imports, à la `typecheck.test.mjs`).
- [ ] Fold in the `.mjs`→`.ts` rename (`todo.md`'s standing bullet) +
      `devtools-protocol` typing while every integration point is
      already being touched; typed CDP events pay off most in the new
      target/session code. (`tsconfig.json` strictness tightening is a
      separate, independent bullet — not subsumed here; its TS7016
      `playwright-core` stub is still needed post-migration since
      Playwright remains a devDependency for tests.)
- [ ] Docs closure: `toy-capture.md`'s `[!TODO]` (Playwright demoted to
      dev/test-only, ratified 2026-07-23) unwraps to descriptive prose
      once this lands; refresh `tap-point.md` and package `CLAUDE.md`
      Key Files.
- [ ] Mutation entries per `Skill(mutation-testing)` for the new shell
      (launch config, session routing, UA override); burn down.

## Open Questions

- Transport: WebSocket (`--remote-debugging-port`) vs pipe
  (`--remote-debugging-pipe`) — puppeteer-core supports both; pipe
  avoids a listening port (nice-to-have for `local-only-operation`
  posture on shared machines).
- Does `launchPersistentContext` behavior (first-window = the profile
  window, no separate about:blank) reproduce cleanly under
  puppeteer-core's `userDataDir`? Affects initial-nav and overlay
  injection timing (`initial_nav.spec.mjs`).
- Rust port relationship: chromiumoxide inherits this architecture
  unchanged, so this migration neither advances nor forecloses it.
  Decide rust only on a concrete forcing function (single-binary
  distribution for chatfs FUSE integration, Node as bottleneck) — see
  `dev.kb/rust-port.md`.

## Success Criteria

- [ ] `pnpm test` green; production path (`har_browse.mjs` import
      graph) contains no Playwright.
- [ ] `user-agent.mjs`, `cache.mjs`, and the `playwright.mjs`
      workarounds deleted; UA suffix behavior preserved
      (tool-identifying suffix per `unblocked-sessions`).
- [ ] Auto-attach (`2026-07-23-001-*`) implementable as a plain API
      call — no transport fights, no dual-client `waitForDebugger`
      contention.
- [ ] Capture parity on the toy server and full synthetic suite;
      BARRIER and drain specs unchanged.

## Notes

The capture-semantics layer (259-line `capture.mjs` core, overlay,
CLI, `cdp_to_har`) transfers conceptually intact — this todo replaces
only the shell. If the browser-extension tap
(`design.kb/070-future-work.kb/capture-implementation-frontier.kb/browser-extension-tap.md`)
is ever pursued, it reuses the same semantics layer against a
`chrome.debugger` host; keeping the seam honest here is what makes that
a host swap rather than a rewrite.
