# 2026-04-24: har-browse CDP pivot

## Focus

Replace `har-browse`'s streaming HAR-entry output with a Chrome DevTools
Protocol event passthrough, shaped to match `chrome-har`'s wire format so
bonafide HAR documents are one downstream call away.

## What Happened

Two completed streaming refactors in sequence, one pivoted at the last
minute:

**Subtask 000** (previous session, committed before this one): HAR-entry
async generator via a `HarTracer` + `toImpl` internal-API bridge. Shipped
and passed tests — then the postscript noted the entry shape was wrong:
an aggregated downstream view dragging an implicit envelope (log.pages,
creator, browser) we discarded. Neither real HAR nor a true event stream.

**Subtask 001** (this session): converted to a CDP event stream. Two
pivots inside one session.

- **Pivot 1 — Playwright public events → CDP events.** First attempt
  subscribed to Playwright's `context.on("request" | "response" | ...)`.
  Required hand-picking fields (live SDK objects don't `JSON.stringify`
  meaningfully — methods instead of enumerable data) plus awaits for
  body/sizes/headers. User reaction: "are the events not public? aren't
  they given to us whole?" That expectation only holds one layer down:
  CDP events are already JSON on the wire. Rewrote `captureEvents` as a
  single `session.emit` override that passes every `Domain.eventName`
  through verbatim.

- **Pivot 2 — ad-hoc shape → chrome-har wire format.** Initial CDP shape
  was `{event, ts, page, params}` with a synthetic `responseBody` event.
  Good for jq but not chrome-har. Investigated `chrome-har` (npm,
  sitespeed.io, v1.2.1 two days ago, actively maintained) and confirmed
  its contract: input is `{method, params}[]`, response body attached at
  `params.response.body` on `Network.responseReceived` with optional
  `.encoding = "base64"`. Rewrote to emit that directly. Zero
  HAR-reconstruction code lives in this repo now — HAR is
  `harFromMessages(messages, {includeTextFromResponseBody: true})` one
  pipe away.

**Also deleted:** `src/playwright/har.mjs` (HarTracer bridge from 000 —
unneeded now) and a ~220-line hand-rolled `events_to_har.mjs` sketch
(written at user's request, rejected by user: "we shouldn't have expert
knowledge in this repo, at all").

## Decisions

**CDP over Playwright events.** Chromium-only is already the status quo
(Crostini, UA probe, persistent context), and CDP events are genuinely
whole in a way Playwright's SDK objects aren't. The blanket `session.emit`
override is ~10 lines and forwards everything; Playwright wrappers would
have been ~60 lines of field-picking and awaits.

**Emit chrome-har's wire format directly, not an adapter in between.**
The wire contract is stable and mechanical; translating at consumer time
would add a 30-line adapter with the same net effect. Emitting the
standard shape lets arbitrary CDP→HAR tooling (chrome-har, puppeteer-har,
etc.) consume our stdout unmodified.

**Don't reconstruct HAR ourselves, ever.** Attempted once at user request
during exploration; user rejected emphatically. HAR is a lossy summary
with many edge cases (redirects, ExtraInfo merging, body encoding,
timings). The expert code exists (chrome-har), is maintained, and is not
in our tree.

## Lessons

**`Network.getResponseBody` is an effectful getter.** Calling it consumes
the body buffer; a second call returns empty. An attempt to simplify by
using both a blanket emit override AND a dedicated
`session.on("Network.responseReceived")` listener double-subscribed the
event. Result: empty bodies (text-len=0 in the e2e test). Fix: fold
body-attachment into the single emit override — hold `responseReceived`
per requestId, flush on `loadingFinished` with body attached.
Single-subscription invariant for effectful CDP calls.

**"The events are public" doesn't mean "the payloads are plain JSON."**
Playwright's Request/Response/Frame objects are live SDK class instances;
the events are semantically public but the payloads aren't serializable
without field-picking. CDP is the layer where payloads are genuinely
plain JSON.

**My "cause" for a fix isn't proof until I isolate it.** Claimed
`getResponseBody`-timing was the cause of a failing variant; user pushed
back. I had no controlled experiment — just "current code works,
previous didn't." The actual cause (double-subscribe) was structural,
not temporal. Lesson: when a fix lands, distinguish "this is the
hypothesis that fit" from "this is the cause I've isolated."

## Next Session

- **`002-cdp2har-validate-chrome-har-consumes-our-stream`** — end-to-end
  smoke test. Our claim that chrome-har consumes our stdout unmodified is
  structural, not empirical. Add a tiny wrapper around `harFromMessages`,
  capture against the toy server, import into DevTools to verify entries,
  bodies, pages, timings.
- **`003-har-browse-handle-epipe-on-stdout-cleanly`** — observed in a
  chatgpt.com capture: piping to an early-exiting consumer dumps an
  unhandled EPIPE stack. ~10 line fix.
