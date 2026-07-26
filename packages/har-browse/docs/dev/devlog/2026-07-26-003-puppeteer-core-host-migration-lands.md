# Devlog: 2026-07-26 — puppeteer-core host migration lands

## Focus

Execute `todo.kb/2026-07-23-002-*`: seam extraction, tripwire, host
swap, UA-subsystem deletion, import-graph guard, docs closure. Landed
across commits `08023cf..df5ed11`. Preceded by the venue-independent
loud post-`end` enqueue item from todo.md (scheduled ahead of the
migration precisely so the churn here wouldn't absorb it silently).

## Decisions

### Seam shape: targets + session factory, not delivered sessions

**Rationale:** `CaptureHost` hands the core opaque targets plus
`session(target)`, rather than ready-made sessions, so the core's
`track(wireSession(t))` covers the CDP-attach latency window — the
exact window `popup_race.spec.mjs` pins. A host that delivered
sessions post-attach would reopen that race by construction.
**Alternatives considered:** async-iterable of sessions (couldn't
express "initial target wired before attach returns" without extra
protocol); delivering sessions via callback (untracked attach window).

### Cut ordering preserved via a deferred promise

The Playwright shell keeps the original order (wire sessions → inject
overlay → start Done/close race) by passing the core a deferred `cut`
promise and resolving it from the race started *after* `captureStream`
returns. Transliteration-faithful; zero behavior change was the goal
of the extraction commit.

### Browser acquisition: Playwright's pinned Chromium, dynamically imported

**Rationale:** already installed, already revision-pinned, and tests
then exercise the identical browser build production captures use
(`unblocked-sessions` fingerprint stability). `$HAR_BROWSE_BROWSER`
overrides. The dynamic import keeps the static production graph
playwright-free, which `tests/import_graph.test.mjs` now guards
(red-verified against the Playwright shell).
**Alternatives considered:** system Chrome (not reliably present in
Crostini containers); `@puppeteer/browsers` (a second browser install
to drift from the test suite's).

### UA probe/cache subsystem deleted (user-ratified trade)

**Rationale:** the probe existed to know the UA *before* launch, which
only Playwright's launch-time `userAgent` option required. The
puppeteer host asks the running browser (`Browser.getVersion`) and
overrides per session — the probe's staleness/mode-parity hazards
cannot arise. 13 UA-scoped mutation entries retired with it;
`cache.mjs` survives because `cachePath` serves the CLI's profile
dirs (the taskfile's "delete cache.mjs" overreached).
**The trade:** launch-time UA branded the whole context; per-session
override leaves popup-first-request and non-page-target traffic
unbranded until `Target.setAutoAttach` (`2026-07-23-001-*`) covers
every target by construction. Ratified in-session by the user after
the regression was surfaced explicitly.

### epipe test goes `--headless`

Its subject is pipe teardown, not windowing; headed startup under the
new host (~4s on Crostini) crowded the 5s guard. The measured-change
caveat in todo.md's flake note is satisfied: the Playwright-internal
`newCDPSession` race it wanted isolated is gone from this path
entirely — the CLI no longer runs Playwright.

## Conventions Established

- **Version-lock playwright, playwright-core, and @playwright/test
  together (exact 1.59.1).** A caret-range re-resolve during the
  devDependency demotion pulled playwright-core 1.62: its registry
  pointed at an uninstalled Chromium (silently broke the CLI's
  executable resolution — empty capture output) and its types clash
  across resolved versions (broke the typecheck gate). Symptom to
  remember: `.pnpm/playwright-core@X` vs `@Y` in a TS2345 error means
  the dedup split.
- Blanket CDP subscription under puppeteer is the mitt-style `'*'`
  wildcard — typed as single-argument but called `(type, payload)`;
  the emit-override hack did not carry over.
- Navigation with commit semantics under puppeteer is raw
  `Page.navigate` (its `goto` has no `commit` lifecycle option).

## Open Questions

- Tripwire 2 (human-driven real-provider login on the new host) is the
  migration's remaining abort condition — batched into the standing
  live `--howto` session along with the hydration forensics.
- A reused puppeteer profile session-restored the prior run's tabs
  once during the smoke (3 initial pages). `--hide-crash-restore-bubble`
  is in the launch args; whether that fully suppresses auto-restore on
  real profiles needs the live session's eyes.
- Transport remains WebSocket (puppeteer default); pipe
  (`--remote-debugging-pipe`) is still the nicer `local-only-operation`
  posture and still unexplored.

## References

- `.claude/todo.kb/2026-07-23-002-Migrate-capture-host-to-puppeteer-core.md`
  — step-by-step status now lives there
- `design.kb/070-future-work.kb/capture-implementation-frontier.md` —
  the ratification record
- Devlog `2026-07-23-002` — the ratification session
- `trash/puppeteer-smoke.mjs` — tripwire-1 harness (gitignored)
