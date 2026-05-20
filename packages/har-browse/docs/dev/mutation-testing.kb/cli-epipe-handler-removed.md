---
status: done
---

# `har_browse.mjs`: stdout error handler removed

Without `process.stdout.on("error", ...)`, an EPIPE from a closed
downstream pipe becomes an unhandled `error` event on stdout — Node's
default is to terminate with an uncaught exception. The browser
context never closes (the finally block runs but the process is gone
before `done` resolves), leaving an orphan Chromium window.

## Injection

`src/har_browse.mjs`: delete the entire `process.stdout.on("error", ...)`
block (and `let stdoutClosed = false` and `if (stdoutClosed) break`).

## Test Coverage

`tests/epipe.test.mjs` — "har-browse | head -n 1 exits cleanly". The
`assert.doesNotMatch(stderr, /Unhandled 'error' event/)` catches the
uncaught-error stack that Node emits when stdout's EPIPE has no
listener. (`assert.doesNotMatch(stderr, /Error: write EPIPE/)` would
catch it too.)
