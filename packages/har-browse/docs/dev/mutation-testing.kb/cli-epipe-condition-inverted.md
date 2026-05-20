---
status: done
---

# `har_browse.mjs`: EPIPE check inverted

`if (err.code === "EPIPE") stdoutClosed = true; else throw err;` —
flip `===` to `!==` and the cases swap: EPIPE rethrows (process
crashes on a normal `head -n 1` consumer) and non-EPIPE errors are
silently swallowed by setting `stdoutClosed = true`. Either failure
mode is user-visible.

## Injection

`src/har_browse.mjs`:

```diff
-  if (err.code === "EPIPE") stdoutClosed = true;
+  if (err.code !== "EPIPE") stdoutClosed = true;
```

## Test Coverage

`tests/epipe.test.mjs` — EPIPE rethrows (else branch), producing the
same "Unhandled 'error' event" stack that the inverted `assert.doesNotMatch`
catches.
