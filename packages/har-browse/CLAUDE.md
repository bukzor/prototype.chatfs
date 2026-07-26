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

puppeteer-core hosts the production capture (`src/host_puppeteer.mjs`;
ratification rationale in
`design.kb/070-future-work.kb/capture-implementation-frontier.md`);
Playwright is a devDependency driving the test suite only -- avoid
introducing it into the production path (guarded intent:
`.claude/todo.kb/2026-07-23-002-*`'s import-graph step).

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
  [--keep-origin-storage] > events.jsonl`.
  Streams until the human clicks the injected "Done Capturing" button
  or closes the window. Profile state persists under
  `${XDG_CACHE_HOME:-$HOME/.cache}/har-browse/profile/<name>`, so
  real-site logins survive across runs.
- `src/capture.mjs` -- venue-agnostic capture semantics
  (`captureStream(host)`): pending-ledger drain, BARRIER, body
  attachment (bodies land at
  `Network.responseReceived.params.response.body`, `.encoding =
  "base64"` when applicable). Consumes the `CaptureHost` seam -- "CDP
  sessions + events per target" plus a cut signal -- defined in the
  same file.
- `src/host_puppeteer.mjs` -- the production host shell behind that
  seam (what the CLI runs): puppeteer-core launcher/profile/transport,
  blanket events via the `'*'` wildcard, per-session branded-UA
  override (`ToolName/Version (+URL)` suffix), `Page.navigate` for
  commit-semantics navigation. Browser executable: `$HAR_BROWSE_BROWSER`,
  else Playwright's pinned Chromium via dynamic import.
- `src/host_playwright.mjs` -- the test suite's host shell, same
  surface: `attachCapture(page)` wires capture onto an existing page
  and returns `{events, done}`; `startCapture(opts)` is the flow
  (launch persistent context + attach + optional origin-storage clear
  + goto).
- `src/inject.mjs` -- persistent Done-button overlay; `addInitScript`
  so it survives navigations, Trusted-Types-safe injection.
- `src/playwright.mjs` -- local-idiom wrapper: inside this package,
  import `chromium` from here, never from `"playwright"`. Strips
  automation tells, applies Crostini-friendly defaults.
- `src/cdp_to_har.mjs` -- CLI (`cdp-to-har`): JSONL stdin -> HAR 1.2
  stdout via chrome-har.
- `src/cache.mjs` -- XDG cache paths (hive-style keys); serves the
  CLI's per-profile directories.
- `toy_server/` -- static toy app on :8000 (`api/conversation`: 6-message
  tree with one fork) for tests and local runs; `toy_pluck.sh` extracts
  that fixture's body from a captured stream.
- `tests/` -- `pnpm test` = node:test units (incl. a `tsc --noEmit`
  typecheck gate) + Playwright e2e against `toy_server/` and
  `tests/_common/server.mjs`.
- `sbin/` -- hand-run tools we build for ourselves (capture forensics,
  live-session probes). Check here before writing an analysis script;
  see `sbin/CLAUDE.md`.

## Protocols

- **Live verification via `--howto`:** when open work needs evidence
  only a real provider session can give, request one -- the human
  drives `har-browse --howto steps.txt` while the agent reads the
  captured stream afterward. Standing policy (user-ratified
  2026-07-26): asking is cheap and welcome; do not leave a todo parked
  on "ask-first" when a session would settle it, and batch related
  checks into one run series. Brief any timing-critical step in chat
  *before* launch and place its instruction ahead of the action in the
  howto file -- the human reads while the page is already live and
  misses short windows otherwise. Protocol lessons (control = pre-fix
  build; cold-load the artifact's own URL): devlog `2026-07-26-002`.
- **Forcing state through the network:** an app that already holds its
  data locally makes no request, and a capture cannot record what never
  crossed the wire. Three settings push against that. Every session gets
  `Network.setCacheDisabled` and `Network.setBypassServiceWorker` at
  wire-up; the CLI additionally wipes the target origin's IndexedDB and
  Cache Storage before navigation (cookies survive -- login state is why
  profiles persist). That clear is **on by default**, because without it
  a cold-loaded claude.ai conversation capture contains none of the
  conversation: verified live 2026-07-26, devlog `2026-07-26-002`.
  `--keep-origin-storage` opts out. The `startCapture` option itself
  defaults off -- primitive versus flow. Coverage:
  `tests/clear_origin_storage.spec.mjs`, `tests/session_settings.spec.mjs`.
- **Done button:** the injected overlay sets
  `#capture-done[data-clicked="true"]` on click; `host_playwright.mjs`
  observes it via `page.waitForFunction` and resolves the seam's cut. DOM-dataset on purpose -- no CDP
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
