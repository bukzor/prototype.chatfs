---
anthropic-skill-ownership: llm-subtask
required-reading:
  - packages/har-browse/.claude/todo.kb/2026-04-24-000-har-browse-streaming-refactor.md
  - packages/har-browse/src/capture.mjs
  - packages/har-browse/src/har_browse.mjs
  - packages/har-browse/src/playwright.mjs
  - packages/har-browse/src/inject.mjs
---

# har-browse: switch from HAR-entry stream to public-events stream

**Priority:** Medium
**Complexity:** Medium (~150 line rewrite of `capture.mjs`, drop
`playwright/har.mjs`, refactor tests)
**Driver:** HAR-entry shape was the wrong seam — see postscript on
`2026-04-24-000-har-browse-streaming-refactor.md`. Replace in place.

## Problem Statement

Current `captureHar` yields HAR entries (Playwright's `harEntry` shape).
That shape is a *fold* — request, response, body, and timings aggregated
into one transaction object — and it carries an implicit envelope (HAR's
`log.pages[]`, `log.creator`, `log.browser`) that we discard, producing
output that is neither real HAR nor a true event stream.

## Proposed Solution

Replace the HAR-entry generator with a Playwright public-events
generator. Each event becomes one JSONL line; no envelope; downstream
folds events into entries (or anything else) if it wants.

### Key design decisions

- **Subscribe at context level, not page level.** Playwright's
  `BrowserContext` re-emits `request`, `response`, `requestfinished`,
  `requestfailed`, etc. for all pages it owns, so we don't have to
  manually rebind on `context.on('page', ...)`.
- **Synthetic IDs.** Assign `p1`, `p2`, ... to pages and `f1`, `f2`,
  ... to frames on first sight (WeakMap → counter). Downstream
  correlates by ID without having to deal with Playwright object
  identity.
- **Body as opaque string.** `response.text()` returns a JS string
  (UTF-8 decoded by Playwright). JS strings are Unicode; JSON encoder
  is lossless on Unicode. Ship it as-is on the `requestfinished` line,
  with the response headers (incl. `content-type`) so downstream knows
  what to do.
- **`start` event header line.** First line of stream is
  `{"event":"start", browser, browserVersion, userAgent, startedAt,
  url}` — self-describing without being an envelope; just one more
  event type.
- **Drop `playwright/har.mjs` entirely.** No more `HarTracer` or
  `toImpl`; pure public API. Removes our one Playwright-internals
  chokepoint.
- **Same termination signal**: injected "Done Capturing" button; window
  close also ends the stream.
- **Same persistent context, same Playwright wrapper, same XDG cache
  profile dir.**

### Initial event set (minimum useful)

| Event              | Source                                     |
| ------------------ | ------------------------------------------ |
| `start`            | synthetic, first line                      |
| `page`             | `context.on('page', ...)` — new page       |
| `framenavigated`   | `context.on('page')` → `page.on(...)`      |
| `domcontentloaded` | page                                       |
| `load`             | page                                       |
| `request`          | context                                    |
| `response`         | context                                    |
| `requestfinished`  | context — carries body + sizes             |
| `requestfailed`    | context                                    |

Defer `console`, `pageerror`, `dialog`, `download`, `websocket`,
`worker` until there's a concrete need.

### Per-event schema sketch

All lines: `{event, ts, ...}`. Page/frame events also include
`page` (and `frame` if applicable). Examples:

```jsonl
{"event":"start","ts":"...","browser":"chromium","browserVersion":"...","userAgent":"...","startedAt":"...","url":"..."}
{"event":"page","ts":"...","page":"p1","url":"about:blank"}
{"event":"framenavigated","ts":"...","page":"p1","frame":"f1","url":"http://..."}
{"event":"request","ts":"...","page":"p1","frame":"f1","method":"GET","url":"...","headers":[...],"postData":null,"resourceType":"document"}
{"event":"response","ts":"...","page":"p1","url":"...","status":200,"statusText":"OK","headers":[...]}
{"event":"requestfinished","ts":"...","page":"p1","url":"...","sizes":{...},"body":"<string>"}
{"event":"requestfailed","ts":"...","page":"p1","url":"...","failure":"net::ERR_..."}
{"event":"load","ts":"...","page":"p1"}
```

## Disposition of existing code

- **Replace in place** — keep `har-browse` bin name and package name
  for this subtask. Renaming is bigger; tracked separately below.
- **Delete** `src/playwright/` (no internal-API needed anymore) and
  `src/playwright/har_test.mjs`.
- **Rewrite** `src/capture.mjs` — rename function (`captureEvents`?
  `captureStream`?) or keep `captureHar` for minimal churn with a
  comment. Lean toward rename — the contract is fundamentally
  different.
- **Rewrite** `src/har_browse.mjs` — same CLI, same flags, just
  consumes new generator and writes events to stdout.
- **Update** `src/test_e2e_example.mjs` — assert on event types instead
  of HAR entries.
- **Update** `toy_pluck.sh` — filter on `event == "requestfinished"`
  and URL match instead of HAR-entry shape.
- **Leave** `src/test_persistent_injection.mjs` alone — it uses
  Playwright directly to verify overlay survival; not affected.

## Implementation Steps

- [ ] Rewrite `src/capture.mjs` as `captureEvents` async generator
  - [ ] Subscribe context-level events (request/response/etc.)
  - [ ] Subscribe page-level events on `context.on('page')` for
        framenavigated, load, domcontentloaded
  - [ ] Synthetic page/frame ID assignment via WeakMap + counter
  - [ ] Emit `start` event before tracer-equivalent setup
  - [ ] `events.on(emitter, ...)` bridge — attach early (lessons from
        previous subtask)
  - [ ] Body fetched via `response.text()` on `requestfinished`,
        inlined as string
  - [ ] Termination: same Done button + context close race; flush
        before emitting `end` to drain in-flight `requestfinished`
        events
- [ ] Rewrite `src/har_browse.mjs` to consume new generator
- [ ] Update `src/test_e2e_example.mjs` to assert on event stream
- [ ] Update `toy_pluck.sh` to filter `requestfinished` events
- [ ] Delete `src/playwright/` directory
- [ ] Update `packages/har-browse/CLAUDE.md` and `README.md`
- [ ] Run full test suite (`pnpm --filter har-browse test`)

## Open Questions

- **Function/script naming.** Keep `captureHar`/`har-browse` (lying
  but minimal churn) or rename to `captureEvents`/`pw-events` (honest
  but bigger blast radius)? Leaning toward keeping the bin name
  (`har-browse`) for now and renaming the function (`captureEvents`).
  Package rename is its own task.
- **`response.text()` failure modes.** What does Playwright do on a
  request that has no body, or a body that hasn't arrived yet? Likely
  empty string and/or rejection. Need to handle gracefully — the
  event line still goes out, just with `body: null` or
  `body: ""`.
- **Ordering guarantees.** Public events fire in real time; do we get
  a strictly monotonic stream, or can `response` for request A
  interleave with `requestfinished` for request B in non-causal ways?
  Probably fine but worth a sanity check.

## Success Criteria

- [ ] Toy server capture produces a stream containing at minimum:
      `start`, `page`, `framenavigated`, `request`/`response`/
      `requestfinished` for `/`, `/index.css`, `/index.js`,
      `/api/conversation`, `load`, `domcontentloaded`
- [ ] No reference to `HarTracer`, `toImpl`, `playwright-core/lib/...`
      anywhere in `src/`
- [ ] `pnpm --filter har-browse test` passes
- [ ] `har-browse | toy_pluck.sh` extracts the api/conversation JSON

## Follow-ups (separate todos)

- Rename package from `har-browse` to something honest
  (`pw-browse`? `browse-stream`?). Touches `packages/`, `package.json`,
  workspace, all docs, devlog references.
- Reconsider `--wait-response` (deferred from previous subtask). With
  events as the seam, this becomes "wait for an event matching a
  pattern" — more general; would be a small CLI feature on top of the
  generator.
- `2026-04-24-002-cdp2har-validate-chrome-har-consumes-our-stream.md`
- `2026-04-24-003-har-browse-handle-epipe-on-stdout-cleanly.md`

## Postscript: final shape (pivoted twice)

**Pivot 1** — from Playwright public events to CDP events. Playwright's
Request/Response/Frame objects are live SDK class instances with no
generic serialization (`JSON.stringify` on them produces `{}`; data lives
behind getter methods and async calls). CDP events, by contrast, are
already JSON on the wire — enabling a single blanket `session.emit`
override that passes every `Domain.event` through verbatim.

**Pivot 2** — from an ad-hoc shape (`{event, ts, page, params}` + a
synthetic `responseBody` event) to `chrome-har`'s wire format
(`{method, params}` with body stashed on
`Network.responseReceived.params.response.body`). Reason: emit the
industry-standard shape so `chrome-har`'s `harFromMessages` consumes our
JSONL unmodified. Zero HAR-reconstruction code lives in this repo; a
bonafide HAR is one `harFromMessages` call away.

**Implementation note — don't double-subscribe an effectful CDP event**:
`Network.getResponseBody` consumes the response body buffer; a second
call returns empty. An early attempt used both a blanket emit override
AND a dedicated `session.on("Network.responseReceived", ...)` listener,
with the listener calling `getResponseBody` inline. Result: empty bodies
(text-len=0 in the e2e test). Fix: fold body-attachment into the single
emit override — hold `responseReceived` per requestId, flush on
`loadingFinished` with body attached. One listener, one `getResponseBody`
call per response.
