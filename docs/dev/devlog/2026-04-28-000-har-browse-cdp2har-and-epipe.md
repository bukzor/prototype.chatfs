# 2026-04-28: har-browse — chrome-har validation + EPIPE handling

## Focus

Two carry-overs from the CDP pivot: prove the central claim of last
session ("our JSONL is consumed by `chrome-har` unmodified") with an
e2e test, and stop dumping a Node stack trace when a downstream
consumer closes the pipe early.

## What Happened

**`002` — chrome-har validation, now empirical.** Added `chrome-har`
1.2.1 as a dep, a `cdp-to-har` bin (~22 lines: stdin JSONL →
`harFromMessages` → HAR 1.2 stdout), and `test_e2e_har.mjs`. The test
spawns the toy server, drives `captureEvents` headless,
fetches `/api/conversation` from the page, runs the captured messages
through `harFromMessages`, and asserts: 4 entries (`/`, `/index.css`,
`/index.js`, `/api/conversation`), `pages[0]` populated, root entry
has `timings` and a numeric `time`, and the `/api/conversation` body
parses as JSON and contains 6 messages. All green.

**`003` — EPIPE guard.** Added a stdout `error` handler in
`har_browse.mjs` that flags EPIPE; the loop checks the flag and
breaks. Breaking lets the generator's `finally` (`context.close()`)
run — important so Chromium isn't orphaned. `test_epipe.mjs` runs a
miniature producer with the same pattern, pipes through
`sed -n 1,1p`, and asserts the producer exits 0 with empty stderr.

**Test ergonomics fix.** `test_e2e_har.mjs` initially used a 500ms
sleep to wait for the toy server. Hit a flaky `ERR_EMPTY_RESPONSE`
when port 8766 was held briefly by a previous run; switched to a
poll-with-fetch loop that retries until the server responds.

## Decisions

**`sed -n 1,1p` instead of `head -1` in the EPIPE test.** Per
`must-read.d/before/ANY-shell-commands.md`: avoid `head` because it
causes SIGPIPE. (Funny: that rule applies to the *test consumer*
here, not the system under test, which is exactly designed to
survive that signal.)

**EPIPE flag-and-break, not `process.exit(0)`.** The subtask file
suggested either; flag-and-break preserves the generator's `finally`,
which closes the browser context. `process.exit` would skip it and
risk a zombie Chromium.

**Test the EPIPE pattern, not the binary.** `har_browse.mjs` waits
on a "Done" click (no headless mode in the bin), so testing
end-to-end EPIPE through the real bin requires either a headless mode
flag (scope creep) or human interaction (not testable). The guard
itself is ~5 lines of generic Node — testing the pattern in a
miniature reproduction gives the same coverage. If the pattern ever
moves into a shared helper, the test moves with it.

**Decode `content.encoding === "base64"` in the test, not at the
emitter.** chrome-har faithfully propagates our `encoding: "base64"`
hint to the HAR `content` block, which is HAR-spec compliant.
Consumers (including our test) decode as needed; we don't pre-decode
at capture time.

## Lessons

**`messages?.length` vs object-shape fixtures.** The toy fixture
keys messages by id (`{messages: {"msg-001": {...}}}`), not as an
array. `apiJson?.messages?.length` quietly returned `undefined`, the
assertion failed, no signal. `Object.keys().length` is the right
probe. Easy to miss when one writes the assertion before re-reading
the fixture.

**`fetch` polling beats `setTimeout` for "wait for server".** Sleep
durations encode a guess about scheduler/OS state and break under
load or port reuse. A retry loop that probes the actual interface is
both faster (no fixed delay) and more reliable.

## Next Session

No carryover from `har-browse`'s todo.md. Plausible next moves
elsewhere in the repo:

- **BB1 → BB2 hand-off**: now that chrome-har produces a real HAR
  end-to-end, the extraction layer can be wired up.
- **chatgpt.com / claude.ai capture sanity check**: the e2e validates
  the toy server only; verifying a real conversation capture
  round-trips through `cdp-to-har` would be cheap insurance before
  building on it.
