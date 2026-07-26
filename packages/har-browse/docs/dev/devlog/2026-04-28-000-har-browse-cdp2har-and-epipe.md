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
run — important so Chromium isn't orphaned. `test_epipe.mjs` spawns
the real bin via `sh -c 'har-browse $URL | head -n 1'`, parses the
first line as JSON, and asserts clean exit + no EPIPE stack in
stderr.

**Test ergonomics fix.** `test_e2e_har.mjs` initially used a 500ms
sleep to wait for the toy server. Hit a flaky `ERR_EMPTY_RESPONSE`
when port 8766 was held briefly by a previous run; switched to a
poll-with-fetch loop that retries until the server responds.

## Decisions

**`head -n 1` is correct here, not `sed`.** The shell-commands rule
to avoid `head` (it causes SIGPIPE) applies to *our* scripts, where
SIGPIPE is undesirable. In this test SIGPIPE is the system under
test. `sed -n '1,1p'` is *not* equivalent: it prints the first line
but keeps reading to EOF, so the producer's pipe never closes —
yields a false positive that quietly waits for a Done click before
"passing."

**`sh -c 'producer | head'` beats Node-mediated piping.** First
attempt wired the consumer's stdin to the producer's `stdout` Stream
via `stdio: [harBrowse.stdout, ...]`. Node holds a read-side ref to
that stream; the OS pipe between the two children isn't direct, so
when `head` exits Node keeps draining and har-browse never sees
EPIPE. Letting `sh` build the pipeline gives a real OS pipe.

**EPIPE flag-and-break, not `process.exit(0)`.** The subtask file
suggested either; flag-and-break preserves the generator's `finally`,
which closes the browser context. `process.exit` would skip it and
risk a zombie Chromium.

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
