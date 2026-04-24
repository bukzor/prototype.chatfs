---
anthropic-skill-ownership: llm-subtask
required-reading:
  - packages/har-browse/CLAUDE.md
  - packages/har-browse/src/capture.mjs
  - packages/har-browse/src/har_browse.mjs
  - packages/har-browse/src/playwright.mjs
  - packages/har-browse/src/playwright/har.mjs
---

# har-browse streaming refactor

**Priority:** Medium
**Complexity:** Medium (~100 line rewrite of `capture.mjs` + new test + CLI)
**Driver:** Skip human "Done Capturing" click on the happy path. User wants:
"if user interaction is honestly zero, avoid presenting the browser, avoid
waiting for interaction."

## Problem Statement

`captureHar` (in `src/capture.mjs`) is **blocking, file-output, human-driven**:
launches browser → injects "Done" overlay → waits for click → writes `.har`
file → returns `{outcome}`. Two limitations follow:

1. No way to terminate early when a watched request succeeds (the happy path
   for automated capture against sites that don't require login).
2. No way to consume captured entries live — downstream BB2 extractor must
   wait for full capture and parse the file.

## Proposed Solution

Refactor `captureHar` to a **streaming, programmatic** function returning
`AsyncGenerator<HarEntry>`. Caller consumes entries via `for await`, calls
`break` to trigger early exit (which closes the context). The "Done" button
remains as a fallback termination signal.

### Architectural decisions (locked this session)

- **Level 3 ownership cut**: don't pass `recordHar` to launch. Instead
  construct `HarTracer` directly with our own delegate, using
  `playwright/har.mjs` re-exports. Reuses Playwright's ~600-line
  event→HAR-entry translator; we own the sink.
- **Streamed shape = HAR entry (`harEntry`)**: same shape Playwright would
  write to the `.har` file, so downstream tooling stays compatible. No
  reshape on the way out.
- **Bridge mechanism**: `async function*` + `node:events`'s `on()` to
  bridge HarTracer's push-based delegate callbacks into the pull-based
  generator. Naturally breaks on context close.
- **Mutability hazard**: `harEntry` objects are mutated in place by
  HarTracer (e.g. content backfilled async). `structuredClone(entry)` at
  yield time is the safe choice.
- **File output becomes caller's concern**: drop `recordHar` from launch
  options; if a `.har` file is wanted, caller (or a small helper)
  reconstructs from the stream via `{log: {version, entries: [...]}}`.

### Why level 3 over alternatives

- **Level 1 (prototype patch)**: smaller, but feels sneaky and hides the
  design from readers
- **Level 6 (rebuild from public events)**: ~600 lines reimplementing what
  Playwright already does carefully; loses HAR fidelity (no `_transferSize`,
  no precise timings, content-body race on navigation)
- **Vendor source**: drift cost on each Playwright bump

Level 3 isolates internal-API dependency to one file
(`src/playwright/har.mjs`) and uses ordinary OO composition everywhere
else.

## Current Situation

**Done this session:**
- Confirmed `HarTracer` / `HarRecorder` architecture (delegate pattern,
  `onEntryFinished` is an empty hook)
- Confirmed in-process: client → server is same V8 isolate; Playwright's
  own `inProcessFactory.js` defines a `toImpl` bridge for exactly this
- Created `src/playwright/har.mjs`: re-exports `HarTracer` (via
  `createRequire` absolute-path bypass of the `exports` map) and `toImpl`
  helper
- Created `src/playwright/har_test.mjs`: smoke test that imports resolve,
  `toImpl` returns a server-side context, `HarTracer` constructs and
  start/stop cycles cleanly. **Not yet executed.**

## Implementation Steps

- [x] Run `src/playwright/har_test.mjs`; passed first try
- [x] Refactor `src/capture.mjs`:
  - [x] Drop `recordHar` from launch options
  - [x] Convert `captureHar` to `async function*` returning HAR entries
  - [x] Construct `HarTracer` with own delegate; use `events.on` bridge
  - [x] Keep "Done" button as termination signal (just closes iterator;
        no sentinel)
  - [x] `structuredClone` entries before yielding
  - [x] On generator close: `tracer.flush()`, `tracer.stop()`,
        `context.close()` — guarded by `contextClosed` flag so we don't
        flush/stop a tracer whose context is already gone
- [x] Update `src/har_browse.mjs`:
  - [x] Drop `--har` flag entirely
  - [x] Stream `JSON.stringify(entry) + "\n"` to stdout
  - **Descoped**: `--wait-response` and early-exit logic — deferred to a
    follow-up subtask
- [x] Update `packages/har-browse/CLAUDE.md`, `README.md`, and
      `toy_pluck.sh` to consume the JSONL entry stream

## Resolved Decisions

- **File output**: dropped `--har` entirely. Caller redirects stdout
  (`har-browse > entries.jsonl`) if file output is wanted. Composable
  with `toy_pluck.sh` via pipe.
- **Termination semantics on the "Done" button**: just closes the
  iterator. No sentinel.
- **`events.on` listener attach timing**: must attach BEFORE
  `tracer.start` — entries fired during `page.goto` are dropped
  otherwise (EventEmitter has no history). First implementation moved
  the `on()` call into the `for await`, lost the first entry. Fixed by
  hoisting `const entries = on(emitter, "entry", { close: ["end"] })`
  above tracer setup.
- **Content backfill timing**: `waitForContentOnStop: true` in the
  HarTracer config makes response bodies present at `onEntryFinished`
  time. Verified via e2e test: 528-byte example.com body captured intact.

## Deferred (follow-up subtask)

- `--wait-response <url-substring>` CLI flag for headless auto-exit
- Headless flag / auto-headless heuristic
- Timeout / failure mode if response never matches

## Success Criteria

- [x] `for await (const entry of captureHar({...}))` yields HAR entries
      live (verified in `test_e2e_example.mjs`)
- [x] Existing manual flow still works (clicks "Done", stream ends)
- [x] `pnpm --filter har-browse test` passes (both unit + e2e)

## Notes

- `src/playwright/har.mjs` is the chokepoint for Playwright internals.
  Any future internal-API drift lands here.
- `toImpl` requires in-process Playwright (`launchPersistentContext`).
  Throws clearly if used over a real transport.

## Postscript: superseded by public-events refactor

After review, the HAR-entry shape proved to be the wrong seam:

- HAR entries are an *aggregated downstream view* (request + response +
  body + timings folded into one transaction). The natural envelope
  comes with them: `{log: {version, creator, browser, pages, entries}}`.
- We emit JSONL of bare entries — neither real HAR (no envelope, no
  pages array, no creator/browser metadata) nor a true event stream.
- The pages array is real loss: page titles and `pageTimings` aren't
  reconstructible from entries alone. We don't emit page lifecycle
  events.
- Per-entry, we leak two Playwright-internal fields (`_frameref`,
  `_monotonicTime`) that Playwright's own serializer strips on file
  output.

The right seam is Playwright's public events (request, response,
requestfinished, framenavigated, load, …). Each event is self-describing
and timestamped; the stream IS the format, no envelope needed. Bonus:
kills the dependency on `HarTracer` / `toImpl` internals.

Follow-up: `2026-04-24-001-pw-browse-public-events-stream.md`.
