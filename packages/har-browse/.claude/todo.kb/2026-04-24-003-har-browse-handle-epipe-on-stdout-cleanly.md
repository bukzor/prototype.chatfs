---
anthropic-skill-ownership: llm-subtask
required-reading:
  - packages/har-browse/src/har_browse.mjs
  - packages/har-browse/src/capture.mjs
---

# har-browse: handle EPIPE on stdout cleanly

**Priority:** Medium
**Complexity:** Low (~10 line fix, plus a test)
**Context:** Observed in the wild on chatgpt.com capture — piping to a
consumer that exits early (e.g. `head`, or any `toy_pluck` that finds what
it wants and bails) kills `har-browse` with a noisy unhandled-error stack:

```
node:events:497
      throw er; // Unhandled 'error' event
      ^
Error: write EPIPE
    at ...writeGeneric... at har_browse.mjs:25:18
  errno: -32, code: 'EPIPE', syscall: 'write'
```

This is standard Unix-pipeline behavior being surfaced as an unhandled
exception because `process.stdout` in Node emits `error` with no default
handler.

## Problem Statement

`har-browse | head -n 20` (or any consumer that closes stdin before
capture ends) should exit quietly with a non-catastrophic status, not dump
a Node stack trace. This is the normal Unix pipeline contract.

## Proposed Solution

In `src/har_browse.mjs`, register an `error` handler on `process.stdout`
that gracefully terminates on EPIPE:

```js
process.stdout.on("error", (err) => {
  if (err.code === "EPIPE") {
    process.exit(0); // or 141 (128 + SIGPIPE) to match coreutils convention
  }
  throw err;
});
```

Alternatively, wrap the `captureEvents` loop in try/catch for EPIPE and
break out cleanly, then await the generator's finally block so the
browser context closes.

## Implementation Steps

- [ ] Add `process.stdout.on("error", ...)` guard in `har_browse.mjs`
- [ ] Ensure generator's `finally` (context.close) still runs — EPIPE
      mid-write shouldn't leak the browser. May require catching inside
      the `for await` loop rather than at process level.
- [ ] Test: `har-browse ... | head -n 1` exits cleanly and the browser
      process terminates (no zombie Chromium).

## Open Questions

- **Exit code on EPIPE**: `0` (consumer got what it wanted, not our
  failure) vs. `141` (POSIX convention for SIGPIPE-killed processes).
  Probably `0` — we're the producer and the consumer's early exit isn't
  our error.
- **Browser cleanup on EPIPE**: Promise.allSettled drain in capture.mjs
  happens after stream close; if EPIPE occurs mid-stream, we need the
  generator's finally (`context.close()`) to run. Verify.

## Success Criteria

- [ ] `har-browse | head -n 1` exits without a stack trace
- [ ] No zombie Chromium after EPIPE
- [ ] Exit code is sensible (0 or 141; document which)
