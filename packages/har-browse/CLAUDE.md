--- # workaround: anthropics/claude-code#13003
depends:
  - Skill(llm-kb)
  - Skill(llm-subtask)
---

# har-browse -- Browser-Driven CDP Capture (chatfs BB1)

Human-in-the-loop capture: launch a persistent-profile Chromium, let the
human browse (login, 2FA, scrolling included), and stream every CDP
event as `{method, params}` JSONL -- chrome-har's wire format. This is
the chatfs pipeline's BB1 (capture) stage; the chatfs-cli-mockup
incubator's provider pluck/splat stages consume its stream. Mission,
requirements, and capture semantics: `design.kb/`.

Playwright hosts the capture today but is ratified for replacement by
puppeteer-core (`.claude/todo.kb/2026-07-23-002-*`; rationale in
`design.kb/050-components.kb/toy-capture.md`) -- avoid deepening
Playwright coupling in new work; it stays as the test-suite driver.

## Current Work

`.claude/todo.md` is the prioritized list; breakdowns in
`.claude/todo.kb/`; deferred ideas in `.claude/ideas.kb/` (notably the
streaming-witness gate and streaming-response-bodies entries). Session
narrative history: `docs/dev/devlog/`. Open session threads: grep
`~/.claude/sessions.kb/` for this directory's `cwd:`. Load
`Skill(llm-subtask)` for maintenance.

## Key Files

- `src/har_browse.mjs` -- CLI (`har-browse`, via package `bin`):
  `har-browse [URL] [--profile NAME] [--howto PATH]
  [--clear-origin-storage] > events.jsonl`.
  Streams until the human clicks the injected "Done Capturing" button
  or closes the window. Profile state persists under
  `${XDG_CACHE_HOME:-$HOME/.cache}/har-browse/profile/<name>`, so
  real-site logins survive across runs.
- `src/capture.mjs` -- the capture core, two surfaces:
  `attachCapture(page)` wires CDP sessions onto an existing page and
  returns `{events, done}`; `startCapture(opts)` is the convenience
  wrapper (launch persistent context + attach + goto). Response bodies
  attach at `Network.responseReceived.params.response.body`
  (`.encoding = "base64"` when applicable).
- `src/inject.mjs` -- persistent Done-button overlay; `addInitScript`
  so it survives navigations, Trusted-Types-safe injection.
- `src/playwright.mjs` -- local-idiom wrapper: inside this package,
  import `chromium` from here, never from `"playwright"`. Threads the
  branded User-Agent, strips automation tells, applies
  Crostini-friendly defaults.
- `src/cdp_to_har.mjs` -- CLI (`cdp-to-har`): JSONL stdin -> HAR 1.2
  stdout via chrome-har.
- `src/cache.mjs`, `src/user-agent.mjs` -- XDG cache paths (hive-style
  keys); UA probe with `ToolName/Version (+URL)` self-identification.
- `toy_server/` -- static toy app on :8000 (`api/conversation`: 6-message
  tree with one fork) for tests and local runs; `toy_pluck.sh` extracts
  that fixture's body from a captured stream.
- `tests/` -- `pnpm test` = node:test units (incl. a `tsc --noEmit`
  typecheck gate) + Playwright e2e against `toy_server/` and
  `tests/_common/server.mjs`.

## Protocols

- **Forcing state through the network:** an app that already holds its
  data locally makes no request, and a capture cannot record what never
  crossed the wire. Three settings push against that. Every session gets
  `Network.setCacheDisabled` and `Network.setBypassServiceWorker` at
  wire-up; `--clear-origin-storage` additionally wipes the target
  origin's IndexedDB and Cache Storage before navigation (cookies
  survive -- login state is why profiles persist). Off by default, since
  whether to force a refetch is provider policy. Coverage:
  `tests/clear_origin_storage.spec.mjs`, `tests/session_settings.spec.mjs`.
- **Done button:** the injected overlay sets
  `#capture-done[data-clicked="true"]` on click; `capture.mjs` observes
  it via `page.waitForFunction`. DOM-dataset on purpose -- no CDP
  round-trip needed from page context.
- **BARRIER marks:** page JS calls `window.harBrowseMark("BARRIER:...")`
  (CDP binding) carrying a page-attested list of the responses it has
  consumed; capture defers each BARRIER's emit until the body-fetches
  in flight at its CDP arrival settle, so every consumed RR precedes
  the BARRIER that names it in the stream. Formal invariant:
  `tests/barrier_consumed.spec.mjs`; mechanics: `src/capture.mjs`
  header comment.

## Design Knowledge

- `design.kb/` -- layered kb (010-mission through 070-future-work).
  Start at `040-design.kb/capture-cut-model.md` when a capture is
  missing data the user saw on screen.
- `docs/dev/mutation-testing.kb/` -- mutation catalog gating test
  hardening; see `Skill(mutation-testing)`.
- `dev.kb/rust-port.md` -- rust-port charter (commit-numbered plan).
